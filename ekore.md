eKore Syntax
============

This file defines the syntax of eKore. The eKore transformations
are defined entirely using kore syntax, with some extra k-frontend
constructs. Hence eKore syntax is simply kore syntax + K Frontend
constructs described using kore.

```k
requires "outer-k.k"

module EKORE-SYNTAX
  imports OUTER-K
endmodule

module EKORE
  imports EKORE-SYNTAX
  configuration <k> $PGM </k>
endmodule
```

