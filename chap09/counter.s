data:       .long 0
entry:      move r3, data
            ld r2, r3, 0
            add r2, r2, 1
            st r2, r3, 0
            halt
