"""Pruebas para la aplicación de facturas."""

# test_reportlab.py
from reportlab.pdfgen import canvas

c = canvas.Canvas("hello.pdf")
c.drawString(100, 100, "Hello World")
c.save()
