---
title: Kicking the MVVM boilerplate with C# 14, without sacrificing compiler safety 
date: 2026-01-31
tags: [.NET, MVVM, tutorial]
---

Nearly every C# developer who's built a GUI application has had to deal with the seemingly infinite code needed to set up two-way binding and asynchronous responses to changing properties. 

Let's consider the following example, where we respond to a change in a string property's value, making sure to consider the dangers of async void and the memory leaks introduced when we forget to unsubscribe from events. 

```csharp
internal class MyViewModel : INotifyPropertyChanged, IDisposable
{
    public event PropertyChangedEventHandler? PropertyChanged;

    private string _myString = string.Empty;
    public string MyString 
    {
        get => _myString;
        set 
        {
            if (EqualityComparer<string>.Default.Equals(_myString, value))
            {
                return;
            }

            _myString = value;
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(MyString)));
        }
    }

    public MyViewModel() 
    {
        PropertyChanged += OnPropertyChanged;
    }

    private async void OnPropertyChanged(object s, PropertyChangedEventArgs e) 
    {
        try 
        {
            if (e.PropertyName != nameof(MyString))
            {
                return;
            }

            // ...
        } 
        catch (Exception ex) 
        {
            // handle...
        }
    };

    public void Dispose() 
    {
        PropertyChanged -= OnPropertyChanged;
    }
}
```

That's about 40 lines of code, and we didn't even implement how we're reacting to the change or handling exceptions from that reaction! Of course, we can reduce the number of times we need to write certain things using methods and inheritance, but this snippet demonstrates just how much you have to write to get set up in the first place. 

The good news is that with C# 14, we can take this whole setup down to just a few lines. Let's see how we get there. 

## C# 14: The "field" keyword

C# 14 introduced the new `field` keyword, which can be used within the context of getters and setters to refer to a private backing field that you haven't explicitly declared. 

This doesn't make a massive difference here, but it stops us from having to declare the `private string _myString` and implement the getter ourselves. It's just one less thing to worry about if we decide to rename the property later on. 

```csharp
public string MyString 
{
    get;
    set 
    {
        if (EqualityComparer<string>.Default.Equals(field, value))
        {
            return;
        }

        field = value;
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(MyString)));
    }
}
```

## CommunityToolkit.Mvvm ObservableObject

CommunityToolkit.Mvvm is a library that's published and maintained by Microsoft, which contains a variety of utilities to facilitate writing code with the MVVM architecture regardless of the UI framework used. 

It provides a helpful abstract class called `ObservableObject` for us, which among other things implements `INotifyPropertyChanged`, and a method `SetProperty<T>(ref T field, T value);`, which performs an equality check, sets a field, and raises the `PropertyChanged` event for us. 

This takes our property definition down to just 5 lines! 

```csharp
internal class MyViewModel : ObservableObject
{
    public string MyString 
    {
        get;
        set => SetProperty(ref field, value);
    }

    // ...
}
```

## C# 14 + CommunityToolkit.Mvvm - Source Generation

Using C# 14 and the community toolkit in tandem, we can save even more space, getting our observable property's definition down to just one line. This only works with C# 14 and above, since the generated code relies on the `field` keyword. Note that we need both our class and our property to be partial, so that the generated source can create the implementation for the getter and setter. 

```csharp
internal partial class MyViewModel : ObservableObject
{
    [ObservableProperty] public partial string MyString { get; set; }

    // ...
}
```

## Fody, For Compile-Time Checks On Event Subscribers

Some familiar with the community toolkit may know that we can use a method with a specific signature to automatically handle changes for a given property, like so: 

```csharp
internal partial class MyViewModel : ObservableObject
{
    [ObservableProperty] public partial string MyString { get; set; }

    private void OnMyStringChanged() 
    {
        // ...
    }
}
```

While this is convenient, there are two glaring issues with this approach. Firstly, it's not immediately clear why `OnMyStringChanged` is called, or in fact, if it will be called at all. Secondly, if we decide to change the name of `MyString` but forget to update the method to match, `OnMyStringChanged` won't be called, and we won't know until it's too late. 

This is why I like to use Fody, an extensible source weaving library. Fody doesn't have Microsoft backing them, instead relying on donations from their community, so if you end up finding value in their libraries, consider [supporting them](https://opencollective.com/fody). 

To set up Fody, you'll need to add packages `Fody` and `Fody.PropertyChanged` to your project. In the root of your project, you'll need to add a file called `FodyWeavers.xml`, with the following content: 

```xml
<Weavers>
  <PropertyChanged />
</Weavers>
```

When you next build the project, Fody will modify this file with XML metadata and namespaces. It will also produce a file called `FodyWeavers.xsd`, which you can safely ignore in version control. 

Now, to use Fody, you can use the `OnChangedMethodAttribute`, whose constructor takes the name of a method in the same class, which will be run when the `PropertyChanged` event is raised for the property. Note that you'll no longer need `partial` modifiers or the `ObservablePropertyAttribute`, but your class must still inherit from `INotifyPropertyChanged`. Here, we keep our inheritance from ObservableObject, so we don't have to satisfy the interface ourselves. 

```csharp
internal class MyViewModel : ObservableObject
{
    [OnChangedMethod(nameof(OnMyStringChanged))]
    public string MyString { get; set; }

    private void OnMyStringChanged() 
    {
        // ...
    }
}
```

This provides both clarity and compiler safety when attaching the method to the property. 

## Conclusion

If we leverage C# 14, CommunityToolkit.Mvvm, and Fody together, we can turn our 45 monstrosity into a safe and comprehensible snippet of just 16 lines. 

```csharp
internal class MyViewModel : ObservableObject
{
    [OnChangedMethod(nameof(OnMyStringChanged))]
    public string MyString { get; set; }

    private async void OnMyStringChanged() 
    {
        try 
        {
            // ...
        } 
        catch (Exception ex)
        {
            // ...
        }
    }
}
```