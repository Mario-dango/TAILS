#include "i2c.h"
#include "lcd_i2c.h"

void Lcd_Send_Cmd(char cmd)
{
	char data_u, data_l;
	uint8_t data_t[4];
	data_u = (cmd & 0xF0);
	data_l = ((cmd<<4) & 0xF0);
	data_t[0] = data_u|0x0C;
	data_t[1] = data_u|0x08;
	data_t[2] = data_l|0x0C;
	data_t[3] = data_l|0x08;
	HAL_I2C_Master_Transmit(&hi2c1, LCD_ADDRESS,(uint8_t*) data_t, 4, 100);
}

void Lcd_Send_Char(char data)
{
	char data_u, data_l;
	uint8_t data_t[4];
	data_u = (data & 0xF0);
	data_l = ((data<<4) & 0xF0);
	data_t[0] = data_u|0x0D;
	data_t[1] = data_u|0x09;
	data_t[2] = data_l|0x0D;
	data_t[3] = data_l|0x09;
	HAL_I2C_Master_Transmit(&hi2c1, LCD_ADDRESS,(uint8_t*) data_t, 4, 100);
}

void Lcd_Init(void)
{
    // 1. Espera inicial de seguridad (el datasheet pide >40ms tras VCC sube a 2.7V)
    HAL_Delay(50);

    // 2. SECUENCIA MÁGICA DE RESET (Hitachi HD44780)
    // Intentamos forzar modo 8-bit tres veces para resetear la máquina de estados interna
    // Nota: Usamos Lcd_Send_Cmd(0x30) repetidamente.
    // Aunque tu función manda 2 nibbles, el LCD interpretará el reset correctamente.

    Lcd_Send_Cmd(0x30);
    HAL_Delay(5);  // Esperar > 4.1ms

    Lcd_Send_Cmd(0x30);
    HAL_Delay(1);  // Esperar > 100us

    Lcd_Send_Cmd(0x30);
    HAL_Delay(10);

    // 3. Ahora sí, pasamos a modo 4-bits
    Lcd_Send_Cmd(0x20); // Function Set: 4-bit interface
    HAL_Delay(10);

    // 4. Configuración Estándar (La que ya tenías)
    Lcd_Send_Cmd(0x28); // 4-bit, 2 líneas, 5x8 puntos
    HAL_Delay(1);

    Lcd_Send_Cmd(0x08); // Display OFF (para evitar parpadeos mientras configuramos)
    HAL_Delay(1);

    Lcd_Send_Cmd(0x01); // Clear Display
    HAL_Delay(2);       // Este comando tarda más, dale 2ms mínimo

    Lcd_Send_Cmd(0x06); // Entry Mode: Increment cursor, no shift
    HAL_Delay(1);

    Lcd_Send_Cmd(0x0C); // Display ON, Cursor OFF, Blink OFF
}

void Lcd_Clear(void)
{
	Lcd_Send_Cmd(0x01);
	HAL_Delay(2);
}

void Lcd_Set_Cursor(int row, int col)
{
	uint8_t address;
	switch(row)
	{
		case 1:
			address = 0x00;
			break;
		case 2:
			address = 0x40;
			break;
		case 3:
			address = 0x14;
			break;
		case 4:
			address = 0x54;
			break;
	}
	address += col - 1;
	Lcd_Send_Cmd(0x80 | address);

}

void Lcd_Send_String(char *str)
{
	while(*str) Lcd_Send_Char(*str++);
}

void Lcd_Shift_Right(void)
{
	Lcd_Send_Cmd(0x1C);
}

void Lcd_Shift_Left(void)
{
	Lcd_Send_Cmd(0x18);
}

void Lcd_Blink(void)
{
	Lcd_Send_Cmd(0x0F);
}

void Lcd_NoBlink(void)
{
	Lcd_Send_Cmd(0x0C);
}

void Lcd_CGRAM_CreateChar(unsigned char pos, const char*msg)
{
    if(pos < 8)
    {
        Lcd_Send_Cmd(0x40 + (pos*8));
        for(unsigned char i=0; i<8; i++)
        {
            Lcd_Send_Char(msg[i]);
        }
    }
}

void Lcd_CGRAM_WriteChar(char pos)
{
    Lcd_Send_Char(pos);
}
