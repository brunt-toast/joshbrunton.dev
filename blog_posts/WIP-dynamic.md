## How dynamic works

Take a look at this code snippet, which makes use of dynamic typing. Looks simple, right? 

```csharp
string[] arr = ["hello", "world"];
dynamic dyn = arr;
int len = dyn.Length;
```

But when we lower it, it becomes this: 

```csharp
using System;
using System.Diagnostics;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Security;
using System.Security.Permissions;
using Microsoft.CSharp.RuntimeBinder;

[assembly: CompilationRelaxations(8)]
[assembly: RuntimeCompatibility(WrapNonExceptionThrows = true)]
[assembly: Debuggable(DebuggableAttribute.DebuggingModes.Default | DebuggableAttribute.DebuggingModes.IgnoreSymbolStoreSequencePoints | DebuggableAttribute.DebuggingModes.EnableEditAndContinue | DebuggableAttribute.DebuggingModes.DisableOptimizations)]
[assembly: SecurityPermission(SecurityAction.RequestMinimum, SkipVerification = true)]
[assembly: AssemblyVersion("0.0.0.0")]
[module: UnverifiableCode]
[module: RefSafetyRules(11)]
internal class Program
{
	[CompilerGenerated]
	private static class <>o__0
	{
		public static CallSite<Func<CallSite, object, object>> <>p__0;

		public static CallSite<Func<CallSite, object, int>> <>p__1;
	}

	private static void Main()
	{
		string[] array = new string[2];
		array[0] = "hello";
		array[1] = "world";
		string[] array2 = array;
		object arg = array2;
		if (<>o__0.<>p__1 == null)
		{
			<>o__0.<>p__1 = CallSite<Func<CallSite, object, int>>.Create(Microsoft.CSharp.RuntimeBinder.Binder.Convert(CSharpBinderFlags.None, typeof(int), typeof(Program)));
		}
		Func<CallSite, object, int> target = <>o__0.<>p__1.Target;
		CallSite<Func<CallSite, object, int>> <>p__ = <>o__0.<>p__1;
		if (<>o__0.<>p__0 == null)
		{
			Type typeFromHandle = typeof(Program);
			CSharpArgumentInfo[] array3 = new CSharpArgumentInfo[1];
			array3[0] = CSharpArgumentInfo.Create(CSharpArgumentInfoFlags.None, null);
			<>o__0.<>p__0 = CallSite<Func<CallSite, object, object>>.Create(Microsoft.CSharp.RuntimeBinder.Binder.GetMember(CSharpBinderFlags.None, "Length", typeFromHandle, array3));
		}
		int num = target(<>p__, <>o__0.<>p__0.Target(<>o__0.<>p__0, arg));
	}
}
```

Even in simple use cases, `dynamic` causes a lot of code to be generated around it. To make it easier to understand, let's strip away all the compiler noise and focus on just what we need to get our same code without typing the `dynamic` keyword ourselves: 

```csharp
static class CallSites
{
    public static CallSite<Func<CallSite, object, object>> GetLengthAsObject;
    public static CallSite<Func<CallSite, object, int>> ConvertLengthObjectToInt;
}

string[] arr = ["hello", "world"];
object dyn = arr;

if (CallSites.ConvertLengthObjectToInt == null)
{
    CallSites.ConvertLengthObjectToInt = CallSite<Func<CallSite, object, int>>.Create(Microsoft.CSharp.RuntimeBinder.Binder.Convert(CSharpBinderFlags.None, typeof(int), typeof(Program)));
}

if (CallSites.GetLengthAsObject == null)
{
    CallSites.GetLengthAsObject = CallSite<Func<CallSite, object, object>>.Create(
        Microsoft.CSharp.RuntimeBinder.Binder.GetMember(
            CSharpBinderFlags.None, 
            "Length", 
            typeof(Program), 
            [CSharpArgumentInfo.Create(CSharpArgumentInfoFlags.None, null)]
        )
    );
}

object lenObj = CallSites.GetLengthAsObject.Target(CallSites.GetLengthAsObject, dyn);
int len = CallSites.ConvertLengthObjectToInt.Target(CallSites.ConvertLengthObjectToInt, lenObj);
```

Let's break down what happens here. 

First, the compiler generates a class to register all the places we'll make use of our dynamic variable, called the "call sites". Nothing is initialised yet, because we don't want to perform the allocations up front - that would increase startup time and waste memory if our code is heuristically unreachable. We'll give them some clear names here: 

```csharp
static class CallSites
{
    public static CallSite<Func<CallSite, object, object>> GetLengthAsObject;
    public static CallSite<Func<CallSite, object, int>> ConvertLengthObjectToInt;
}
```

When we assign to a dynamic variable, we really just assign to an object. Every type in C# derives from object, so this cast is always safe. 

```csharp
string[] arr = ["hello", "world"];
object dyn = arr;
```

When we want to execute dynamic code, we need to define what our call sites are going to do. The statement `int len = dynamic.Length` can be expressed in two stages: Locate the object known as `arr.Length`, then convert it to an `int`. The below code builds that logic using reflection and stores it in our `CallSites` class for later re-use. 

```csharp 
if (CallSites.GetLengthAsObject == null)
{
    CallSites.GetLengthAsObject = CallSite<Func<CallSite, object, object>>.Create(
        Microsoft.CSharp.RuntimeBinder.Binder.GetMember(
            CSharpBinderFlags.None, 
            "Length", 
            typeof(Program), 
            [CSharpArgumentInfo.Create(CSharpArgumentInfoFlags.None, null)]
        )
    );
}

if (CallSites.ConvertLengthObjectToInt == null)
{
    CallSites.ConvertLengthObjectToInt = CallSite<Func<CallSite, object, int>>.Create(Microsoft.CSharp.RuntimeBinder.Binder.Convert(CSharpBinderFlags.None, typeof(int), typeof(Program)));
}
```

Then, we run the targets, extracting `object lenObj` and then converting it into `int len`. 

```csharp
object lenObj = CallSites.GetLengthAsObject.Target(CallSites.GetLengthAsObject, dyn);
int len = CallSites.ConvertLengthObjectToInt.Target(CallSites.ConvertLengthObjectToInt, lenObj);
```

The targets will throw `RuntimeBinderException` if they cannot execute. 

Of course, the generated code will vary wildly depending on how the dynamic is assigned and consumed. Consistent among all applications is that the compiler will treat the dynamic as an object and construct mini-interpreters to try to execute the code at runtime. 

## Dynamic APIs in compiled libraries 

While `dynamic` variables are essentially `objects`, built assemblies' public APIs still need to be able to reconstruct the information that a symbol is of a dynamic type so consumers can treat it as such. This is done with an attribute, `System.Runtime.CompilerServices.DynamicAttribute`. It is reserved for compiler usage, meaning that it is a compiler error for user code to annotate any symbol with it. 

Consider the lowering of the following method signature with a dynamic parameter:

```csharp
void M(dynamic dyn);
void M([Dynamic] object dyn);
```

Or, for a dynamic return type, we annotate the entire method with a return attribute: 

```csharp
dynamic M();

[return: Dynamic]
object M();
```

If we use any generic type parameters, we pass `bool[] transformFlags` to the constructor to indicate which parameters were dynamic. The order they appear in `transformFlags` is the same order in which they are read, for example: 

```csharp
void M(Dictionary<object,dynamic> dyn);

void M([Dynamic([false, false, true])] Dictionary<object,object> dyn)
```