#ifndef INC_LCD_I2C_H_
#define INC_LCD_I2C_H_

#define LCD_ADDRESS 0x4E
//#define LCD_ADDRESS 0x3F
//#define LCD_ADDRESS 0x27

void Lcd_Init(void);
void Lcd_Send_Cmd(char cmd);
void Lcd_Send_Char(char data);
void Lcd_Send_String(char *str);
void Lcd_Set_Cursor(int row, int col);
void Lcd_Clear(void);
void Lcd_Shift_Right(void);
void Lcd_Shift_Left(void);
void Lcd_Blink(void);
void Lcd_NoBlink(void);
void Lcd_CGRAM_CreateChar(unsigned char pos, const char*msg);
void Lcd_CGRAM_WriteChar(char pos);

#endif
