"""Comando para inicializar los métodos de pago predeterminados."""

from django.core.management.base import BaseCommand

from pagos.views import inicializar_metodos_pago


class Command(BaseCommand):
    """Comando para inicializar los métodos de pago predeterminados en el sistema."""

    help = "Inicializa los métodos de pago predeterminados"

    def handle(self, *_: list, **__: dict) -> None:
        """
        Ejecuta el comando para inicializar los métodos de pago.

        Args:
            *_: Argumentos posicionales (no utilizados).
            **__: Opciones del comando (no utilizadas).

        Returns:
            None

        """
        metodos_pago = inicializar_metodos_pago()
        self.stdout.write(
            self.style.SUCCESS(
                f"Se han inicializado {metodos_pago} métodos de pago correctamente",
            ),
        )
