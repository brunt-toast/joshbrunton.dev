If you try to use string interpolation while logging, CA2254 (from `Microsoft.Extensions.Logging.Abstractions`) recommends that "The logging message template should not vary between calls to `LoggerExtensions.Log*`". This is because when logging, parameters should be given names, so that an implementation can allow for easier filtering logs by the values of these properties. 

```csharp
_logger.LogInformation($"User {userName} logged in"); // Warning: CA2254
_logger.LogInformation("User {userName} logged in", userName); // Correct version 
```

A caveat of this is that many ILogger implementations, including the default in most app hosts, will fail silently in the event of a parameter count mismatch. There is some merit to this decision - you probably don't want a failed log event to throw an exception. 

```csharp
_logger.LogInformation("User {userName} logged in at {dateTime}", userName); 
// fails quietly because we didn't pass {dateTime}
```

Fortunately, it's possible to catch parameter count mismatches at compile time, with warning CA2017. To ensure that logging never fails in this way, you can promote the warning to a compiler error. In an SDK-style project, or better yet in `Directory.Build.props` (to apply to all projects), add: 

```xml
<PropertyGroup>
    <WarningsAsErrors>
        $(WarningsAsErrors);CA2017
    </WarningsAsErrors>
</PropertyGroup>
```

>[!TIP]
> You may also want to treat CA2254 as an error to prevent the use of string interpolation during logging. 

You can also add this validation to youur own methods methods, such as extensions on ILogger or your own implementation (so long as `Microsoft.Extensions.Logging.Abstractions` is installed). 

First, declare this attribute in any namespace. Note that the class and property name must match exactly what is in this example. 

```csharp
[AttributeUsage(AttributeTargets.Method)]
public sealed class MessageTemplateFormatMethodAttribute : Attribute
{
    public string FormatParameterName { get; }

    public MessageTemplateFormatMethodAttribute(string formatParameterName)
    {
        FormatParameterName = formatParameterName;
    }
}
```

Then, use the attribute on a method, giving it the name of the method's template parameter. Remember to use `nameof()` instead of a "magic string" in case you decide to rename the parameter later. 

```csharp
[MessageTemplateFormatMethod(nameof(template))]
public static void LogCustom(this ILogger source, string template, params object?[]? arguments)
{
    // ...
}
```

Now, you can rest assured that every log event will succeed and be properly parameterised. 