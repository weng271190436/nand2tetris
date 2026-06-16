// Fill.asm
// When the user presses a
// keyboard key (any key), the
// entire screen becomes black
// Equivalent to filling addresses 16384 to 24575
// with -1


(MAIN)
    @KBD            // KBD address
    D=M             // D = KBD (0 if no key, non-zero if key pressed)
    @FILL           // label for fill routine
    D;JNE           // if D != 0 (key pressed), jump to FILL
    @MAIN           // else jump back to MAIN
    0;JMP           // unconditional jump back to loop

(FILL)
    @SCREEN
    D=A
    @count
    M=D         // count = 16384 (start of screen memory)

(LOOP)
    @count
    D=M             // D = count
    @KBD
    D=D-A           // D = D - KBD (24576)
    @END
    D;JEQ           // if count == KBD (24576), jump to END

    @count
    A=M
    M=-1            // RAM[count] = -1 (fill screen with black)

    @count
    M=M+1       // count = count + 1

    @LOOP
    0;JMP       // go back to LOOP

(END)
    @END
    0;JMP       // infinite loop to stop
