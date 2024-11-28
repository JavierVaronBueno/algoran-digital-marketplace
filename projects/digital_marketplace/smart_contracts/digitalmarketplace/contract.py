"""
Módulo para la implementación de un contrato inteligente en Algorand que representa un marketplace digital.

Este contrato permite la creación de un marketplace donde se pueden gestionar activos digitales (ASA)
para su compra y venta entre usuarios. El creador del contrato puede establecer el precio de los activos
y los compradores pueden adquirir una cantidad específica. Al finalizar, el creador puede reclamar las
ganancias y liberar los recursos mínimos del contrato.

Clases:
    Digitalmarketplace: Clase principal que implementa el contrato inteligente.

Métodos:
    - create_application: Inicializa la aplicación con el ID de un activo y su precio unitario.
    - opt_in_to_asset: Permite que la aplicación realice un opt-in al activo definido.
    - set_price: Define o modifica el precio unitario del activo.
    - buy: Permite a los compradores adquirir una cantidad específica de activos.
    - delete_application: Elimina la aplicación y transfiere las ganancias y activos restantes al creador.

Autores:
    - [Nombre del desarrollador o equipo]

Licencia:
    - [Tipo de licencia, e.g., MIT]
"""

from algopy import ARC4Contract, Asset, Global, Txn, UInt64, arc4, gtxn, itxn


class Digitalmarketplace(ARC4Contract):
    """
    Clase que implementa un marketplace digital en Algorand.

    Esta clase permite la creación, gestión y eliminación de una aplicación
    descentralizada (DApp) para el comercio de activos digitales.
    """

    # Global State
    asset_id: UInt64  # Identificador del activo ASA
    unitary_price: UInt64  # Precio unitario del activo

    # Creación del contrato o la aplicación DApp
    @arc4.abimethod(allow_actions=["NoOp"], create="require")
    def create_application(self, asset_id: Asset, unitary_price: UInt64) -> None:
        """
        Inicializa la aplicación con el ID de un activo y su precio unitario.

        Parámetros:
            asset_id (Asset): El identificador del activo ASA.
            unitary_price (UInt64): El precio unitario del activo.

        Guarda el ID del activo y su precio en el estado global de la aplicación.
        """
        # Guardar un número de Asset ID
        self.asset_id = asset_id.id
        # Guardar un precio unitario
        self.unitary_price = unitary_price

    # Usuario vendedor enviará assets al contrato
    @arc4.abimethod
    def opt_in_to_asset(
        self,
        mbr_pay: gtxn.PaymentTransaction,  # Transacción de pago dentro de una transacción grupal o transacciones atómicas
    ) -> None:
        """
        Permite que la aplicación realice opt-in al activo.

        Parámetros:
            mbr_pay (gtxn.PaymentTransaction): Transacción de pago para cubrir los costos de opt-in.

        Condiciones:
            - Solo el creador del contrato puede realizar esta acción.
            - La aplicación no debe haber hecho opt-in previamente.
            - El pago debe cubrir el saldo mínimo requerido.
        """
        # Verifica que el que envía sea el creador del contrato; esta acción solo la puede hacer el creador
        assert Txn.sender == Global.creator_address

        # Verifica que ya no se haya hecho opt-in
        assert not Global.current_application_address.is_opted_in(Asset(self.asset_id))

        # Verifica que el receptor del pago sea la aplicación
        assert mbr_pay.receiver == Global.current_application_address

        # Verifica el balance mínimo de la aplicación
        assert mbr_pay.amount == Global.min_balance + Global.asset_opt_in_min_balance

        # Lógica de la transacción interna
        itxn.AssetTransfer(
            xfer_asset=self.asset_id,  # Asset a enviar
            asset_receiver=Global.current_application_address,  # Quien recibe es la misma aplicación
            asset_amount=0,  # Al enviar cero tokens, se da permiso a la red para interactuar con ese asset
        ).submit()

    # Usuario vendedor define el precio de venta de los assets
    @arc4.abimethod
    def set_price(self, unitary_price: UInt64) -> None:
        """
        Define o modifica el precio unitario del activo.

        Parámetros:
            unitary_price (UInt64): El nuevo precio unitario del activo.

        Condiciones:
            - Solo el creador del contrato puede modificar el precio.
        """
        # Verifica que el que modifica el precio sea el creador del contrato; esta acción solo la puede hacer el creador
        assert Txn.sender == Global.creator_address
        # Edita el precio unitario
        self.unitary_price = unitary_price

    # Usuario comprador puede hacer la compra de n assets
    @arc4.abimethod
    def buy(
        self,
        quantity: UInt64,  # Cantidad de assets a comprar
        buyer_txn: gtxn.PaymentTransaction,  # Transacción de pago dentro de una transacción grupal o transacciones atómicas
    ) -> None:
        """
        Permite a un comprador adquirir una cantidad específica del activo.

        Parámetros:
            quantity (UInt64): La cantidad de activos a comprar.
            buyer_txn (gtxn.PaymentTransaction): Transacción de pago asociada.

        Condiciones:
            - El precio unitario debe ser mayor a cero.
            - El comprador debe enviar el pago correspondiente al contrato.
        """
        # Verificar que el precio de venta sea diferente de cero
        assert self.unitary_price != UInt64(0)

        # Verificar que el que está enviando la transacción de pago sea el mismo que está llamando al método
        assert buyer_txn.sender == Txn.sender

        # Verificar que el pago que se está haciendo sea a la cuenta del contrato inteligente
        assert buyer_txn.receiver == Global.current_application_address

        # Verificar el monto que se está pagando para comprar los assets
        assert buyer_txn.amount == self.unitary_price * quantity

        # Hacer que el contrato envíe la transacción interna de transferencia de assets
        itxn.AssetTransfer(
            xfer_asset=self.asset_id,  # Asset a comprar
            asset_receiver=Txn.sender,  # El contrato a quien le va a enviar ese asset
            asset_amount=quantity,  # Monto a transferir
        ).submit()

    # Usuario vendedor puede reclamar las ganancias y assets sobrantes
    @arc4.abimethod(allow_actions=["DeleteApplication"])
    def delete_application(self) -> None:
        """
        Elimina la aplicación y transfiere las ganancias y activos restantes al creador.

        Condiciones:
            - Solo el creador del contrato puede realizar esta acción.

        Al eliminar la aplicación:
            - Se reclaman los activos restantes.
            - Se transfieren las ganancias y se libera el saldo mínimo.
        """
        # Verifica que el que elimina el contrato sea el creador del contrato; esta acción solo la puede hacer el creador
        assert Txn.sender == Global.creator_address

        # Reclamar el saldo de los productos
        itxn.AssetTransfer(
            xfer_asset=self.asset_id,  # Asset a enviar al creador
            asset_receiver=Global.creator_address,  # Se le envía al creador
            asset_amount=0,  # Se le envía un monto de cero
            asset_close_to=Global.creator_address,  # Eliminamos el permiso de interactuar con el asset y enviamos el saldo al creador
        ).submit()

        # Reclamar la ganancia de Algos
        itxn.Payment(
            receiver=Global.creator_address,  # Quien recibe es el creador
            amount=0,  # Monto a recuperar, cero
            close_remainder_to=Global.creator_address,  # Se envían los Algos de ganancias y el balance mínimo
        ).submit()
