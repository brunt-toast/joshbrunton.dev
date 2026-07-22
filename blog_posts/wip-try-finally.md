
```csharp
class Program 
{
    public static int Main(string[] args)
    {
        int i = global::System.Random.Shared.Next(0,0);
        try 
        {
            return i;
        }
        finally 
        {
            global::System.Console.WriteLine("Hello world");
        }
    }
}
```

```asm
; Assembly listing for method Program:Main(System.String[]):int (FullOpts)
; Emitting BLENDED_CODE for X64 with AVX - Windows
; FullOpts code
; optimized code
; rbp based frame
; fully interruptible
; No PGO data
; 0 inlinees with PGO data; 1 single block inlinees; 0 inlinees without PGO data

G_M000_IG01:
       push     rbp
       push     rbx
       sub      rsp, 40
       lea      rbp, [rsp+0x30]
       mov      qword ptr [rbp-0x10], rsp

G_M000_IG02:
       test     byte  ptr [(reloc)], 1
       je       SHORT G_M000_IG06

G_M000_IG03:
       mov      rcx, 0xD1FFAB1E
       mov      rcx, gword ptr [rcx]
       xor      edx, edx
       xor      r8d, r8d
       mov      rax, qword ptr [rcx]
       mov      rax, qword ptr [rax+0x40]
       call     [rax+0x30]System.Random:Next(int,int):int:this
       mov      ebx, eax

G_M000_IG04:
       mov      rcx, 0xD1FFAB1E
       call     [System.Console:WriteLine(System.String)]
       mov      eax, ebx

G_M000_IG05:
       add      rsp, 40
       pop      rbx
       pop      rbp
       ret

G_M000_IG06:
       mov      rcx, 0xD1FFAB1E
       call     CORINFO_HELP_GET_GCSTATIC_BASE
       jmp      SHORT G_M000_IG03

G_M000_IG07:
       push     rbp
       push     rbx
       sub      rsp, 40
       mov      rbp, qword ptr [rcx+0x20]
       mov      qword ptr [rsp+0x20], rbp
       lea      rbp, [rbp+0x30]

G_M000_IG08:
       mov      rcx, 0xD1FFAB1E
       call     [System.Console:WriteLine(System.String)]
       nop

G_M000_IG09:
       add      rsp, 40
       pop      rbx
       pop      rbp
       ret

; Total bytes of code 139
```

IG01 prologue - bookkeeping related to try/finally funclet 
IG02 - check that Random.Shared has been init'd. If yes, fall to IG03; if no, jump to IG06. 

IG03 - 
`mov rcx, 0xD1FFAB1E` creates a reference to Random.Shared 
`mov rcx, gword ptr [rcx]` - de-references rcx 
`xor edx, edx` - sets `edx` to 0 (by xoring it with itself)
`xor r8d r82` - sets `r8d` to 0
`mov rax, qword ptr [rcx]` - load the Random.Shared's method table pointer from its first machine word
`mov rax, qword ptr [rax+0x40]` - load another pointer from the method table, basically to Random.Next(int,int)
`call [rax+0x30]System.Random:Next(int,int):int:this` - does the random.shared 
`mov ebx, eax` - copies the return value `eax` into `ebx`, a hidden field we'll restore later (THIS IS WHY MODDING IT LATER DOES NOTHING)

IG04 - Executes finally then prepares return. 
`mov rcx, 0xD1FFAB1E` - Loads managed string ref for "Hello world" into rcx 
`call...` does writeline 
`mov eax, ebx` - moves the prevously saved value of `i` back into the return register. 

IG05 - 
`add rsp, 40` releases the stack space we reserved earlier 
`pop rbx` restores our original rbx
`pop rbp` returns the caller's stack frame pointer 
`ret` returns to the caller 

6 - Random.Shared init path. Used if it fails in IG02. 
7 - prologue for 8. Basically the same as IG01.  
8 - executes the finally, in the case that an exception was thrown instead of happy return 
9 - epilogue for 8. Basically the same as IG05. 
