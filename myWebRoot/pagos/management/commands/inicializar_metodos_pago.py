from django.core.management.base import BaseCommand
from pagos.models import MetodoPago

class Command(BaseCommand):
    help = 'Inicializa los métodos de pago predeterminados'

    def handle(self, *args, **kwargs):
        metodos_pago = [
            {
                'tipo': 'nequi',
                'nombre': 'Nequi',
                'activo': True,
                'configuracion': {'descripcion': 'Pago móvil rápido y seguro'}
            },
            {
                'tipo': 'bancolombia',
                'nombre': 'Bancolombia',
                'activo': True,
                'configuracion': {'descripcion': 'Transferencia bancaria'}
            },
            {
                'tipo': 'pse',
                'nombre': 'PSE',
                'activo': True,
                'configuracion': {'descripcion': 'Pago seguro electrónico'}
            },
            {
                'tipo': 'tarjeta',
                'nombre': 'Tarjeta de Crédito',
                'activo': True,
                'configuracion': {'descripcion': 'Visa, MasterCard, American Express'}
            },
            {
                'tipo': 'transferencia',
                'nombre': 'Transferencia Bancaria',
                'activo': True,
                'configuracion': {'descripcion': 'Transferencia desde cualquier banco'}
            },
            {
                'tipo': 'movil',
                'nombre': 'Pago Móvil',
                'activo': True,
                'configuracion': {'descripcion': 'Pagos desde tu celular'}
            }
        ]
        
        for metodo in metodos_pago:
            MetodoPago.objects.get_or_create(
                tipo=metodo['tipo'],
                defaults={
                    'nombre': metodo['nombre'],
                    'activo': metodo['activo'],
                    'configuracion': metodo['configuracion']
                }
            )
            
        self.stdout.write(
            self.style.SUCCESS(f'Se han inicializado {len(metodos_pago)} métodos de pago correctamente')
        )