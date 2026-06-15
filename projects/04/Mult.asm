// Mult.asm
// Computes R2 = R0 * R1
// Uses repeated addition

    @R2
    M=0         // R2 = 0 (initialize result)

    @R1
    D=M         // D = R1
    @count
    M=D         // count = R1

(LOOP)
    @count
    D=M         // D = count
    @END
    D;JEQ       // if count == 0, jump to END

    @R0
    D=M         // D = R0
    @R2
    M=D+M       // R2 = R2 + R0

    @count
    M=M-1       // count = count - 1

    @LOOP
    0;JMP       // go back to LOOP

(END)
    @END
    0;JMP       // infinite loop to stop
