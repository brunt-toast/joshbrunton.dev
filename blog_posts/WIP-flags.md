Having too many boolean properties on a class can often be considered a code smell. It makes it difficult to grasp and verbose to query. Enums are often used in place of mutually exclusive boolean properties, but they can also be used for non-exclusive information too, with a little bit of bitwise logic. 

In C#, it is customary to annotate enums which will be subjected to such logic with `[Flags]`. It's usually also a good idea to define `None = 0`. Subsequent values must be powers of 2, which can be expressed in a variety of ways, commonly in binary or by bit-shifting the number 1 to the left. For convenience, members can also be defined as combinations of other members using the binary OR operator (`|`). 

```csharp
[Flags]
enum SandwichToppings 
{
    None = 0,
    
    Egg = 0b_0001,
    Mayo = 0b_0010,

    Cheese = 1 << 2,
    Tomato = 1 << 3,

    EggSalad = Egg | Mayo,
}
```

To check if a flags enum value has a specific set, you can use the equation `(value & x)`. If the result equals `x` exactly, the flag is present; otherwise, it's not. The below example checks for the existence of mayo.

```txt
  0b_0011       Mayo | Egg
& 0b_0010       Mayo 
---------
  0b_0010       Mayo 
= 0b_0010       Mayo 
--------- 
     true
```

This also works with combination members, e.g., does an egg+mayo+cheese sandwich contain egg salad? 

```txt
  0b_0111       Cheese | Mayo | Egg
& 0b_0011                Mayo | Egg
---------      
  0b_0011                Mayo | Egg
= 0b_0011                Mayo | Egg
--------- 
     true
```

