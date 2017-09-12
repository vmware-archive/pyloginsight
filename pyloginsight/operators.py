# -*- coding: utf-8 -*-

# String operators are case-insensitive filters that can be applied to text fields:
CONTAINS = "CONTAINS "
NOT_CONTAINS = "NOT_CONTAINS "
HAS = "HAS "
NOT_HAS = "NOT_HAS "
MATCHES_REGEX = "~="
NOT_MATCHES_REGEX = "!~="
_STRING = [CONTAINS, NOT_CONTAINS, HAS, NOT_HAS, MATCHES_REGEX, NOT_MATCHES_REGEX]

# Time operators
LAST = "LAST"
_TIME = [LAST]

# Boolean operators
EXISTS = "EXISTS"
_BOOLEAN = [EXISTS]

# Numeric operators can be applied to fields that contain numbers
NOTEQUAL = "!="
EQUAL = "="
GT = ">"
LT = "<"
GE = ">="
LE = "<="
_NUMERIC = [NOTEQUAL, EQUAL, GT, LT, GE, LE, LAST]
