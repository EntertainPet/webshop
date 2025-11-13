# EntertainPet

## Initial Build
https://ev.us.es/ultra/courses/_101203_1/outline/file/_5649317_1

## Deployment

````
$ python manage.py runserver
````

## DB
Cada vez que efectuemos cambios sobre los models sera necesario:
```
$ python manage.py makemigrations
$ python manage.py migrate 
```

## Stripe

numero de tarjeta de prueba: 4242424242424242
la fecha de caducidad tiene que ser posterior a la actual y el cvv cualquiera

## Tables

![tables](assets/tables.png)

## Routes

![routes](assets/routes.png)