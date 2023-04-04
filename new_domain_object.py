class Level:
    __slots__ = ('operator', 'operand_to_consume', 'parent', 'terms')
    operator: 'str'
    operand_to_consume: 'int'  # None means infinity (for the root one)
    parent: 'Level | None'
    terms: 'list'

    def __init__(self, operator, operand_to_consume, parent, terms):
        self.operator = operator
        self.operand_to_consume = operand_to_consume
        self.parent = parent
        self.terms = terms

    def __str__(self):
        terms_str = '\n  '.join(
            str(term).replace('\n', '\n  ') if isinstance(term, Level) else str(term)
            for term in self.terms
        )
        return f"{self.operator}:\n  {terms_str}"

class Domain:

    def __init__(self, domain_list) -> None:
        self.to_recursive_domain(domain_list)

    def __str__(self) -> str:
        return str(self.root_level)

    def to_recursive_domain(self, domain_list):
        self.root_level = Level('&', len(domain_list), None, [])
        current = self.root_level

        for term in domain_list:
            if current.operator == term:
                if term == '!':
                    # forget this double negation
                    current = current.parent
                    continue
                current.operand_to_consume += 1
            elif term in ('&', '|', '!'):  # term is a operator but not the same than the current level
                current.operand_to_consume -= 1
                new_level = Level(term, 2 if term != '!' else 1, current, [])
                current = new_level
            else:
                current.terms.append(term)
                current.operand_to_consume -= 1

            while current.operand_to_consume == 0 and current.parent is not None:
                current.parent.terms.append(current)
                current = current.parent

    def materialize(self, model):
        # Materialize no-store field with search method and _name_search (x2x =/ilike,in <string>)
        pass

    def optimize(self, model):
        # Optimize the domain, return a new Domain optimized and bind with a model
        pass

    def constraint_by(self, field_name):
        # return the value if the domain ensure that field_name = <value>
        pass

if __name__ == '__main__':
    print("Domain 1 :", [('<leaf1>')])
    print(Domain([('<leaf1>')]))

    print("Domain 2 :", [('<leaf1>'), ('<leaf2>'), ('<leaf3>')])
    print(Domain([('<leaf1>'), ('<leaf2>'), ('<leaf3>')]))

    print("Domain 3 :", ['|', ('<leaf1>'), ('<leaf2>')])
    print(Domain(['|', ('<leaf1>'), ('<leaf2>')]))

    print("Domain 4 :", ['&', '|', ('<leaf1>'), ('<leaf2>'), '|', ('<leaf3>'), ('<leaf4>')])
    print(Domain(['&', '|', ('<leaf1>'), ('<leaf2>'), '|', ('<leaf3>'), ('<leaf4>')]))

    print("Domain 5 :", ['&', '|', '|', ('<leaf1>'), ('<leaf2>'), ('<leaf3>'), ('<leaf4>')])
    print(Domain(['&', '|', '|', ('<leaf1>'), ('<leaf2>'), ('<leaf3>'), ('<leaf4>')]))

    print("Domain 6 :", ['&', '!', '|', ('<leaf1>'), ('<leaf2>'), '|', ('<leaf3>'), ('<leaf4>')])
    print(Domain(['&', '!', '|', ('<leaf1>'), ('<leaf2>'), '|', ('<leaf3>'), ('<leaf4>')]))

    print("Domain 7 :", ['&', '!', '!', '|', ('<leaf1>'), ('<leaf2>'), '|', ('<leaf3>'), ('<leaf4>')])
    print(Domain(['&', '!', '!', '|', ('<leaf1>'), ('<leaf2>'), '|', ('<leaf3>'), ('<leaf4>')]))

