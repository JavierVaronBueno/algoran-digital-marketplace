from algopy import ARC4Contract, Asset, Global, Txn, UInt64, arc4, gtxn, itxn


class Digitalmarketplace(ARC4Contract):
    # Global State
    asset_id: UInt64
    unitary_price: UInt64

    # Creacion del contrato o la aplicación Dapp
    @arc4.abimethod(allow_actions=["NoOp"], create="require")
    def create_application(self, asset_id: Asset, unitary_price: UInt64) -> None:
        # Guardar un numero de asset ID
        self.asset_id = asset_id.id
        # Guardar un precio unitario
        self.unitary_price = unitary_price

    # Usuario vendedor enviara assets al contrtato <------SEGUNDA PARTE

    # Hacer que el contrato haga opt in al asset
    @arc4.abimethod
    def opt_in_to_asset(
        self,
        mbr_pay: gtxn.PaymentTransaction,  # Transaccion de pago dentro de una transaccion grupal o transacciones atomicas
    ) -> None:
        # Verifica que el que envia sea el creador del contrato, esta accion solo la puede hacer el creador
        assert Txn.sender == Global.creator_address

        # Verifica de que ya no se halla echo opt in
        assert not Global.current_application_address.is_opted_in(Asset(self.asset_id))

        # Verifica que el receptor del pago sea la aplicacion
        assert mbr_pay.receiver == Global.caller_application_address

        # Balance de la aplicacion
        assert mbr_pay.amount == Global.min_balance + Global.asset_opt_in_min_balance

        # Logica de la transaccion interna
        itxn.AssetTransfer(
            xfer_asset=self.asset_id,  # Asset a enviar
            asset_receiver=Global.current_application_address,  # Quien recibe es la misma aplicacion
            asset_amount=0,  # Al enviarme cero tokens estoy dando permisos a la red para que interactue con ese asset
        ).submit()

    # Usuario vendedor defina el precio de venta de los assets
    @arc4.abimethod
    def set_price(self, unitary_price: UInt64) -> None:
        # Verifica que el que modifica el precio sea el creador del contrato, esta accion solo la puede hacer el creador
        assert Txn.sender == Global.creator_address
        # Edita el precio unitario
        self.unitary_price = unitary_price

    # Usuario comprador puede hacer la compra de n assets
    @arc4.abimethod
    def buy(
        self,
        quantity: UInt64,  # Cantidad de assets a comprar
        buyer_txn: gtxn.PaymentTransaction,  # Transaccion de pago dentro de una transaccion grupal o transacciones atomicas
    ) -> None:
        # Verificar que el precio de venta sea diferente de cero
        assert self.unitary_price != UInt64(0)

        # Verificar que el que esta enviando la transaccion de pago sea el mismo que esta llamando al metodo
        assert buyer_txn.sender == Txn.sender

        # Verificar que el pagao que se esta haciendo sea a la la cuenta del contrato inteligente
        assert buyer_txn.receiver == Global.current_application_address

        # Verificar el monto que se esta pagando para comprar los asset
        assert buyer_txn.amount == self.unitary_price * quantity

        # Hacer que el contrato envie la transaccion interna de transferencia de assets
        itxn.AssetTransfer(
            xfer_asset=self.asset_id,  # Asset a comprar
            asset_receiver=Txn.sender,  # El contrato a quien le va enviar ese asset a que cuenta
            asset_amount=quantity,  # Monto a transferir
        ).submit()

    # Usuario vendedor pueda reclamar las ganancias y assets sobrantes
    # Hacer esto es siempre recomendado para librerar siempre esos 0.001 algos del balance minimo
    @arc4.abimethod(allow_actions=["DeleteApplication"])
    def delete_application(self) -> None:
        # Verifica que el que elimina el contrato sea el creador del contrato, esta accion solo la puede hacer el creador
        assert Txn.sender == Global.creator_address

        # Reclamar el saldo de los productos
        itxn.AssetTransfer(
            xfer_asset=self.asset_id,  # Asset a enviar al creador
            asset_receiver=Global.creator_address,  # Se le envia al creador
            asset_amount=0,  # Se le envia un monto de cero
            asset_close_to=Global.creator_address,  # Eliminamos el permios de interactuar con el asset y envia el saldo a una cuenta espesifica
        ).submit()

        # Reclamar  la ganancia de algos
        itxn.Payment(
            receiver=Global.creator_address,  # Quein recibe es el creador
            amount=0,  # monto a recuperar de cero
            close_remainder_to=Global.creator_address,  # Se envia los algos de ganancias y ademas se le envia el balance minimo
        ).submit()
