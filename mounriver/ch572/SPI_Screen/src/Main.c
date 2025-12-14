#include "CH57x_common.h"
#include "gc9a01.h"
#include "spi.h"
#include <math.h>
#include <stdlib.h>

// DebugInit ...

#define BALL_R 15
#define BALL_D (BALL_R * 2)
#define BALL_BUF_SIZE (BALL_D * BALL_D * 2)

// Sprite Buffer (Green Ball on Black Background)
uint8_t ballBuffer[BALL_BUF_SIZE] __attribute__((aligned(4)));

void InitBallSprite() {
  uint16_t green = GREEN;
  uint8_t g_hi = green >> 8;
  uint8_t g_lo = green & 0xFF;

  uint16_t black = BLACK;
  uint8_t b_hi = black >> 8;
  uint8_t b_lo = black & 0xFF;

  int idx = 0;
  for (int y = 0; y < BALL_D; y++) {
    for (int x = 0; x < BALL_D; x++) {
      // Distance from center (r-0.5 to center in 0..2r-1 coords)
      float cx = (float)x - BALL_R + 0.5f;
      float cy = (float)y - BALL_R + 0.5f;
      float d2 = cx * cx + cy * cy;

      if (d2 <= (BALL_R * BALL_R)) {
        ballBuffer[idx++] = g_hi;
        ballBuffer[idx++] = g_lo;
      } else {
        ballBuffer[idx++] = b_hi;
        ballBuffer[idx++] = b_lo;
      }
    }
  }
}

int main() {
  // Initialize common delay/clock
  SetSysClock(CLK_SOURCE_HSE_PLL_60MHz);

  // Initialize SPI with clock divider 2 (Max Speed)
  SPI_Init(16);

  // Initialize Display
  GC9A01_Init();

  GC9A01_FillScreen(BLACK);

  InitBallSprite();

  // Ball Properties
  float x = 120.0f, y = 120.0f; // Center of screen
  float vx = 2.7f, vy = 3.14f;
  int r = BALL_R;
  int R_SCREEEN = 120;
  int R_LIMIT = R_SCREEEN - r;
  float R_LIMIT_SQ = (float)(R_LIMIT * R_LIMIT);

  while (1) {
    int old_x = (int)x - r;
    int old_y = (int)y - r;
    int size = r * 2;

    // 2. Update Physics
    x += vx;
    y += vy;

    // 3. Collision Detection (Circular)
    float rx = x - 120.0f;
    float ry = y - 120.0f;
    float distSq = rx * rx + ry * ry;

    if (distSq >= R_LIMIT_SQ) {
      float dist = sqrtf(distSq);

      // Normal vector
      float nx = rx / dist;
      float ny = ry / dist;

      // Reflect
      float dot = vx * nx + vy * ny;
      vx = vx - 2.0f * dot * nx;
      vy = vy - 2.0f * dot * ny;

      // Randomness
      vx += ((rand() % 20) - 10) * 0.05f;
      vy += ((rand() % 20) - 10) * 0.05f;

      // Push ball back inside
      float overlap = dist - R_LIMIT;
      x -= nx * (overlap + 0.5f);
      y -= ny * (overlap + 0.5f);
    }

    // 4. Update Graphic
    int new_x = (int)x - r;
    int new_y = (int)y - r;

    // Erase Old Trail (Difference between Old Rect and New Rect)
    // Horizontal Erase
    if (new_x > old_x) {
      GC9A01_FillRect(old_x, old_y, new_x - old_x, size, BLACK);
    } else if (new_x < old_x) {
      GC9A01_FillRect(new_x + size, old_y, old_x - new_x, size, BLACK);
    }

    // Vertical Erase
    if (new_y > old_y) {
      GC9A01_FillRect(old_x, old_y, size, new_y - old_y, BLACK);
    } else if (new_y < old_y) {
      GC9A01_FillRect(old_x, new_y + size, size, old_y - new_y, BLACK);
    }

    // Draw New Ball Sprite (Overwrites its own box with Green Circle/Black
    // Corners)
    GC9A01_DrawBitmap(new_x, new_y, size, size, ballBuffer);

    // 6. Delay (Optional)
    // mDelaymS(2);
  }
}
