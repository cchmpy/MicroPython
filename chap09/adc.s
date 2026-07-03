data:   .long 0       
entry:  move r3, data
        adc r1,0,5          
        st r1, r3, 0  
        halt 