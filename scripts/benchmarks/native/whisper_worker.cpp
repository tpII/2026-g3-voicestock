// Persistent CPU worker for the pinned whisper.cpp evaluation build.
#include "whisper.h"
#include <chrono>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

using Clock = std::chrono::steady_clock;
static double elapsed(Clock::time_point start) {
    return std::chrono::duration<double>(Clock::now() - start).count();
}
static std::string quoted(const std::string &text) {
    std::string out = "\"";
    for (unsigned char c : text) {
        if (c == '"' || c == '\\') { out += '\\'; out += c; }
        else if (c == '\n') out += "\\n";
        else if (c == '\r') out += "\\r";
        else if (c == '\t') out += "\\t";
        else if (c >= 32) out += c;
    }
    return out + '"';
}
int main(int argc, char **argv) {
    if (argc != 3) return 2;
    auto start = Clock::now();
    auto cp = whisper_context_default_params();
    cp.use_gpu = false;
    auto *ctx = whisper_init_from_file_with_params(argv[1], cp);
    if (!ctx) return 3;
    std::cout << "{\"load_s\":" << elapsed(start) << "}" << std::endl;
    std::string path;
    while (std::getline(std::cin, path)) {
        std::ifstream file(path, std::ios::binary | std::ios::ate);
        if (!file || file.tellg() <= 0 || file.tellg() % 4 != 0) {
            std::cout << "{\"error\":\"invalid float32 input\"}" << std::endl;
            continue;
        }
        std::vector<float> samples(static_cast<size_t>(file.tellg()) / 4);
        file.seekg(0);
        file.read(reinterpret_cast<char *>(samples.data()), samples.size() * 4);
        auto p = whisper_full_default_params(WHISPER_SAMPLING_GREEDY);
        p.n_threads = std::stoi(argv[2]);
        p.language = "es";
        p.translate = false;
        p.no_context = true;
        p.print_progress = p.print_realtime = p.print_timestamps = false;
        p.temperature = 0;
        p.temperature_inc = 0;
        p.greedy.best_of = 1;
        p.vad = false;
        start = Clock::now();
        int code = whisper_full(ctx, p, samples.data(), samples.size());
        double seconds = elapsed(start);
        std::string text;
        for (int i = 0; code == 0 && i < whisper_full_n_segments(ctx); ++i)
            text += whisper_full_get_segment_text(ctx, i);
        std::cout << "{\"inference_s\":" << seconds << ",\"text\":" << quoted(text)
                  << ",\"error\":" << (code ? "\"whisper_full failed\"" : "null")
                  << "}" << std::endl;
    }
    whisper_free(ctx);
}
