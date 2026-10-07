#Requires -Version 5.1
#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Configures one Windows Ethernet adapter for the VoiceStock local network.

.DESCRIPTION
    Assigns the persistent static address 192.168.50.2/24 to the adapter named
    by -InterfaceAlias. DHCP is disabled on that adapter. No default gateway
    and no DNS server are configured for it. Other adapters, including Wi-Fi,
    are not modified.

.EXAMPLE
    .\scripts\setup_pc_ethernet.ps1 -InterfaceAlias "Ethernet"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$InterfaceAlias
)

$ErrorActionPreference = "Stop"

$VoiceStockAddress = "192.168.50.2"
$VoiceStockPrefixLength = 24

function Write-Info {
    param([string]$Message)
    Write-Host "==> $Message"
}

function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-SelectedAdapter {
    param([string]$Alias)

    $adapters = @(Get-NetAdapter -ErrorAction Stop | Where-Object { $_.Name -eq $Alias })
    if ($adapters.Count -eq 0) {
        $knownAdapters = @(Get-NetAdapter -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name)
        $knownList = "none"
        if ($knownAdapters.Count -gt 0) {
            $knownList = $knownAdapters -join ", "
        }
        throw "No network adapter is named '$Alias'. Adapters on this PC: $knownList"
    }
    if ($adapters.Count -gt 1) {
        throw "More than one network adapter is named '$Alias'. Refusing to choose one."
    }
    return $adapters[0]
}

function Get-IPv4Addresses {
    param([string]$Alias)
    return @(Get-NetIPAddress -InterfaceAlias $Alias -AddressFamily IPv4 -ErrorAction SilentlyContinue)
}

function Test-VoiceStockAddress {
    param($Address)
    return ($Address.IPAddress -eq $VoiceStockAddress -and $Address.PrefixLength -eq $VoiceStockPrefixLength)
}

function Clear-InterfaceIPv4DnsServers {
    param([string]$Alias)

    # ResetServerAddresses restores the DHCP DNS list. address=none stores a
    # static IPv4 DNS configuration with no servers on this adapter only.
    Write-Info "Setting no IPv4 DNS servers on '$Alias'..."
    & netsh.exe interface ipv4 set dnsservers "name=$Alias" source=static address=none validate=no | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Could not configure '$Alias' with no IPv4 DNS servers."
    }
}

if (-not (Test-Administrator)) {
    throw "Administrator permissions are required. Open PowerShell as Administrator and run this script again."
}

if ($InterfaceAlias -match '[*?\[\]]') {
    throw "InterfaceAlias must be the exact adapter name, without wildcard characters."
}
if ([string]::IsNullOrWhiteSpace($InterfaceAlias)) {
    throw "InterfaceAlias is required. Example: .\scripts\setup_pc_ethernet.ps1 -InterfaceAlias `"Ethernet`""
}

foreach ($commandName in @("Get-NetAdapter", "New-NetIPAddress", "Get-DnsClientServerAddress")) {
    if (-not (Get-Command $commandName -ErrorAction SilentlyContinue)) {
        throw "Windows networking cmdlets are unavailable ($commandName). Run this script on Windows PowerShell."
    }
}
if (-not (Get-Command netsh.exe -ErrorAction SilentlyContinue)) {
    throw "netsh.exe is required to configure the selected adapter with no IPv4 DNS servers."
}

$adapter = Get-SelectedAdapter -Alias $InterfaceAlias
if ($adapter.Status -eq "Disabled") {
    throw "Adapter '$InterfaceAlias' is disabled. Enable that adapter and run this script again. No other adapter was changed."
}

$mediaType = [string]$adapter.MediaType
$physicalMedium = [string]$adapter.NdisPhysicalMedium
$isWiFi = ($mediaType -eq "Native 802.11") -or ($physicalMedium -eq "Native802_11") -or ($physicalMedium -eq "WirelessLan") -or ($physicalMedium -eq "WirelessWan")
if ($isWiFi) {
    throw "Adapter '$InterfaceAlias' is a Wi-Fi adapter. Pass the Ethernet adapter cabled to the Raspberry Pi. Wi-Fi was not modified."
}

Write-Info "Configuring only adapter '$InterfaceAlias'."

Write-Info "Disabling IPv4 DHCP on '$InterfaceAlias'..."
Set-NetIPInterface -InterfaceAlias $InterfaceAlias -AddressFamily IPv4 -Dhcp Disabled -Confirm:$false

$defaultRoutes = @(Get-NetRoute -InterfaceAlias $InterfaceAlias -AddressFamily IPv4 -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue)
foreach ($route in $defaultRoutes) {
    Write-Info "Removing IPv4 default route via $($route.NextHop) on '$InterfaceAlias'..."
    Remove-NetRoute -InterfaceAlias $InterfaceAlias -DestinationPrefix "0.0.0.0/0" -NextHop $route.NextHop -Confirm:$false
}

Clear-InterfaceIPv4DnsServers -Alias $InterfaceAlias

$addresses = @(Get-IPv4Addresses -Alias $InterfaceAlias)
$exactAddresses = @($addresses | Where-Object { Test-VoiceStockAddress $_ })
$otherAddresses = @($addresses | Where-Object { -not (Test-VoiceStockAddress $_) })

foreach ($address in $otherAddresses) {
    Write-Info "Removing $($address.IPAddress)/$($address.PrefixLength) from '$InterfaceAlias'..."
    Remove-NetIPAddress -InterfaceAlias $InterfaceAlias -IPAddress $address.IPAddress -PrefixLength $address.PrefixLength -Confirm:$false
}

if ($exactAddresses.Count -gt 1) {
    foreach ($address in $exactAddresses) {
        Remove-NetIPAddress -InterfaceAlias $InterfaceAlias -IPAddress $address.IPAddress -PrefixLength $address.PrefixLength -Confirm:$false
    }
    $exactAddresses = @()
}

if ($exactAddresses.Count -eq 1) {
    Write-Info "IPv4 address $VoiceStockAddress/$VoiceStockPrefixLength is already set on '$InterfaceAlias'."
} else {
    Write-Info "Assigning $VoiceStockAddress/$VoiceStockPrefixLength on '$InterfaceAlias'..."
    New-NetIPAddress `
        -InterfaceAlias $InterfaceAlias `
        -AddressFamily IPv4 `
        -IPAddress $VoiceStockAddress `
        -PrefixLength $VoiceStockPrefixLength `
        -Confirm:$false | Out-Null
}

$configured = @(Get-IPv4Addresses -Alias $InterfaceAlias | Where-Object { Test-VoiceStockAddress $_ })
$unexpected = @(Get-IPv4Addresses -Alias $InterfaceAlias | Where-Object { -not (Test-VoiceStockAddress $_) })
$remainingDefaultRoutes = @(Get-NetRoute -InterfaceAlias $InterfaceAlias -AddressFamily IPv4 -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue)
$ipInterface = Get-NetIPInterface -InterfaceAlias $InterfaceAlias -AddressFamily IPv4
$dns = Get-DnsClientServerAddress -InterfaceAlias $InterfaceAlias -AddressFamily IPv4
$dnsServers = @()
if ($null -ne $dns.ServerAddresses) {
    $dnsServers = @($dns.ServerAddresses | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
}

$failures = @()
if ($configured.Count -ne 1) {
    $failures += "adapter does not have $VoiceStockAddress/$VoiceStockPrefixLength"
} else {
    Write-Info "OK: '$InterfaceAlias' has $VoiceStockAddress/$VoiceStockPrefixLength."
}
if ($unexpected.Count -ne 0) {
    $failures += "adapter still has another IPv4 address"
}
if ($ipInterface.Dhcp -ne "Disabled") {
    $failures += "IPv4 DHCP is still enabled"
} else {
    Write-Info "OK: IPv4 DHCP is disabled on '$InterfaceAlias'."
}
if ($remainingDefaultRoutes.Count -ne 0) {
    $failures += "adapter still has an IPv4 default route"
} else {
    Write-Info "OK: '$InterfaceAlias' has no IPv4 default gateway."
}
if ($dnsServers.Count -ne 0) {
    $failures += "adapter still has IPv4 DNS servers"
} else {
    Write-Info "OK: '$InterfaceAlias' has no IPv4 DNS server."
}

if ($failures.Count -gt 0) {
    throw "Ethernet configuration is not in the required state: $($failures -join '; ')."
}

Write-Info "Wi-Fi was not modified. No adapter other than '$InterfaceAlias' was changed."
Write-Info "The address is stored in the persistent Windows network configuration and survives reboot."
