from kobold.compare import CompareRule


class AssertIn(CompareRule):
    def __init__(self, acceptable_values):
        self.acceptable_values = acceptable_values
        super().__init__(rule='assert_in')
        

    def __str__(self):
        return 'compare_rule: included in {}'.format(
            self.acceptable_values
        )

    def compare_with(self, other_thing, *args, **kwargs):
        return other_thing in self.acceptable_values
