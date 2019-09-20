from django.db import models

class Temperature(models.Model):
    leftSensorTemperature = models.FloatField()
    middleSensorTemperature = models.FloatField()
    rightSensorTemperature = models.FloatField()
    tankSensorTemperature = models.FloatField()
    dateOfReading = models.DateTimeField()