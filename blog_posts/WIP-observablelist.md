The ObservableCollection class (from `System.Collections.ObjectModel`) is great for a variety of applications, but it starts to ache when you're doing non-trivial work while adding or removing large amounts of data. If you don't need to react to every update individually, this `BatchObservableList` will save several redundant calls. 

We'll start with a class that implements `IList<T>` and `INotifyCollectionChanged`, and wraps a `List<T>` (we don't use the interface since we rely on the AddRange method). For every method that might cause an insertion or deletion on the underlying list, we'll check if anything changed, and fire off our event if so. 

```csharp
public class BatchObservableList<T> : IList<T>, INotifyCollectionChanged
{
    private readonly List<T> _data = [];

    public event NotifyCollectionChangedEventHandler? CollectionChanged;

    public void Add(T item)
    {
        _data.Add(item);
        CollectionChanged?.Invoke(this, new NotifyCollectionChangedEventArgs(NotifyCollectionChangedAction.Add));
    }

    public void Clear()
    {
        _data.RemoveAll(_ => true);
        CollectionChanged?.Invoke(this, new NotifyCollectionChangedEventArgs(NotifyCollectionChangedAction.Reset));
    }

    public bool Remove(T item)
    {
        bool ret = _data.Remove(item);
        if (ret)
        {
            CollectionChanged?.Invoke(this, new NotifyCollectionChangedEventArgs(NotifyCollectionChangedAction.Remove));
        }
        return ret;
    }

    public void Insert(int index, T item)
    {
        _data.Insert(index, item);
        CollectionChanged?.Invoke(this, new NotifyCollectionChangedEventArgs(NotifyCollectionChangedAction.Add));
    }

    public void RemoveAt(int index)
    {
        _data.RemoveAt(index);
        CollectionChanged?.Invoke(this, new NotifyCollectionChangedEventArgs(NotifyCollectionChangedAction.Remove));
    }

    public T this[int index]
    {
        get => _data[index];
        set
        {
            _data[index] = value;
            CollectionChanged?.Invoke(this, new NotifyCollectionChangedEventArgs(NotifyCollectionChangedAction.Add));
        }
    }
}
```

But the real magic starts to happen with `AddRange` and `RemoveAll`. Since they have direct access to the underlying list, we can fire our collection changed only once after potentially hitting more than one list entry. 

```csharp
public class BatchObservableList<T> : IList<T>, INotifyCollectionChanged
{
    // ...

    public void AddRange(IEnumerable<T> items)
    {
        _data.AddRange(items);
        CollectionChanged?.Invoke(this, new NotifyCollectionChangedEventArgs(NotifyCollectionChangedAction.Add));
    }

    public void RemoveAll(Predicate<T> predicate)
    {
        if (_data.RemoveAll(predicate) > 0)
        {
            CollectionChanged?.Invoke(this, new NotifyCollectionChangedEventArgs(NotifyCollectionChangedAction.Remove));
        }
    }
}
```

Finally, we just have to add in the read-only methods on `IList<T>`, which map directly to their counterparts on our internal list. 

```csharp
public class BatchObservableList<T> : IList<T>, INotifyCollectionChanged
{
    // ...

    public bool Contains(T item) => _data.Contains(item);

    public void CopyTo(T[] array, int arrayIndex) => _data.CopyTo(array, arrayIndex);

    public int Count => _data.Count;

    public bool IsReadOnly => false;

    public int IndexOf(T item) => _data.IndexOf(item);

    public IEnumerator<T> GetEnumerator() => _data.GetEnumerator();

    IEnumerator IEnumerable.GetEnumerator() => _data.GetEnumerator();
}
```

And ta-da! An observable collection implementation that doesn't burn your RAM when updating in bulk.