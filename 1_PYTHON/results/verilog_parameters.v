
// Generated Parameters for Tang Nano 4K Sobel Implementation
// Date: 2025-10-28 12:22:14

// Image dimensions
parameter IMG_WIDTH = 640;
parameter IMG_HEIGHT = 480;

// Data widths
parameter PIXEL_WIDTH = 8;
parameter ADDR_WIDTH = 10;
parameter COUNTER_WIDTH = 10;
parameter SOBEL_WIDTH = 11;

// Line buffer size
parameter LINE_BUFFER_SIZE = IMG_WIDTH;

// Sobel kernels (as parameters)
parameter signed [SOBEL_WIDTH-1:0] SOBEL_Gx [0:8] = {
    -1,  0,  1,
    -2,  0,  2, 
    -1,  0,  1
};

parameter signed [SOBEL_WIDTH-1:0] SOBEL_Gy [0:8] = {
    -1, -2, -1,
     0,  0,  0,
     1,  2,  1  
};

// Clock domains (estimates for Tang Nano 4K)
parameter CLK_CAMERA = 25_000_000;    // 25 MHz camera clock
parameter CLK_PROCESS = 75_000_000;   // 75 MHz processing clock  
parameter CLK_HDMI = 25_000_000;      // 25 MHz HDMI pixel clock (VGA)
