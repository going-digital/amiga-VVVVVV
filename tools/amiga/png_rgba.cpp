// Host-only PNG decoding through the repository's existing LodePNG dependency.
#include "lodepng.h"
#include <cstdio>
#include <vector>
int main(int argc, char **argv) {
    if (argc != 2) return 2;
    std::vector<unsigned char> pixels;
    unsigned w, h;
    unsigned error = lodepng::decode(pixels, w, h, argv[1]);
    if (error) { std::fprintf(stderr, "%s\n", lodepng_error_text(error)); return 1; }
    std::printf("%u %u\n", w, h);
    return std::fwrite(pixels.data(), 1, pixels.size(), stdout) == pixels.size() ? 0 : 1;
}
