from django.db import models

class Item(models.Model):
    name = models.CharField(max_length=30),
    description = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class Showcase(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.item.id)

