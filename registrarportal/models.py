from django.db import models
from datetime import date


def add_school_year(start_year, year):
    try:
        return start_year.replace(year=start_year.year + year)
    except ValueError:
        return start_year.replace(year=start_year.year + year, day=28)


class schoolYear(models.Model):
    start_on = models.DateField()
    until = models.DateField()
    modified_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return " ".join(map(str, [self.start_on.strftime("%Y"), "-", (add_school_year(self.start_on, 1)).strftime("%Y")]))

    def display_sy(self):
        return " ".join(map(str, [self.start_on.strftime("%Y"), "-", (add_school_year(self.start_on, 1)).strftime("%Y")]))
