Place the original Excel workbook here.

Expected filename:

```text
data/source/鸣潮动作数据汇总.xlsx
```

Some extraction tools may preserve the escaped fallback name instead:

```text
data/source/#U9e23#U6f6e#U52a8#U4f5c#U6570#U636e#U6c47#U603b.xlsx
```

The Mornye source guard tries both names and fails loudly if neither exists.
This file is not required to be committed if it is large or private.
