from algopy import ARC4Contract, Asset, Global, Txn, UInt64, arc4, gtxn, itxn


class Digitalmarketplace(ARC4Contract):
    """
    A reusable base model for Algorand ARC-4 smart contracts.
    This contract implements a digital marketplace where assets can be managed,
    priced, purchased, and claimed.

    Attributes:
        asset_id (UInt64): The ID of the asset managed by the contract.
        unitary_price (UInt64): The unit price of the asset.
    """

    # Global State
    asset_id: UInt64
    unitary_price: UInt64

    @arc4.abimethod(allow_actions=["NoOp"], create="require")
    def create_application(self, asset_id: Asset, unitary_price: UInt64) -> None:
        """
        Initializes the contract by setting the asset ID and unitary price.

        Parameters:
            asset_id (Asset): The asset to be managed by this contract.
            unitary_price (UInt64): The unit price of the asset.
        """
        # Store the asset ID
        self.asset_id = asset_id.id
        # Store the unitary price
        self.unitary_price = unitary_price

    @arc4.abimethod
    def opt_in_to_asset(self, mbr_pay: gtxn.PaymentTransaction) -> None:
        """
        Opts the contract into the asset.

        This method allows the contract to interact with a specified asset by opting in.

        Validations:
            - Only the contract creator can call this method.
            - The application must not already be opted-in to the asset.
            - The receiver of the payment must be the application.
            - The payment amount must meet the minimum balance requirements.

        Parameters:
            mbr_pay (gtxn.PaymentTransaction): A payment transaction covering the opt-in costs.
        """
        # Ensure only the creator can perform this action
        assert Txn.sender == Global.creator_address

        # Ensure the application is not already opted-in to the asset
        assert not Global.current_application_address.is_opted_in(Asset(self.asset_id))

        # Ensure the receiver of the payment is the application
        assert mbr_pay.receiver == Global.current_application_address

        # Ensure the payment meets minimum balance requirements
        assert mbr_pay.amount == Global.min_balance + Global.asset_opt_in_min_balance

        # Perform the internal asset transfer for opting in
        itxn.AssetTransfer(
            xfer_asset=self.asset_id,  # Asset to opt into
            asset_receiver=Global.current_application_address,  # Application receives the asset
            asset_amount=0,  # Zero tokens are sent, enabling opt-in
        ).submit()

    @arc4.abimethod
    def set_price(self, unitary_price: UInt64) -> None:
        """
        Sets the unit price of the asset.

        Validations:
            - Only the contract creator can set the price.

        Parameters:
            unitary_price (UInt64): The new unit price of the asset.
        """
        # Ensure only the creator can modify the price
        assert Txn.sender == Global.creator_address
        # Update the unit price
        self.unitary_price = unitary_price

    @arc4.abimethod
    def buy(self, quantity: UInt64, buyer_txn: gtxn.PaymentTransaction) -> None:
        """
        Allows a user to purchase assets from the contract.

        Validations:
            - The unit price must not be zero.
            - The sender of the payment transaction must match the caller.
            - The receiver of the payment must be the smart contract.
            - The payment amount must match the expected price.

        Parameters:
            quantity (UInt64): Number of assets to purchase.
            buyer_txn (gtxn.PaymentTransaction): Payment transaction included in a grouped transaction.
        """
        # Ensure the unit price is greater than zero
        assert self.unitary_price != UInt64(0)

        # Ensure the sender of the payment matches the caller
        assert buyer_txn.sender == Txn.sender

        # Ensure the payment is directed to the smart contract
        assert buyer_txn.receiver == Global.current_application_address

        # Ensure the payment amount matches the expected price
        assert buyer_txn.amount == self.unitary_price * quantity

        # Perform the internal transaction to transfer assets
        itxn.AssetTransfer(
            xfer_asset=self.asset_id,  # Asset to transfer
            asset_receiver=Txn.sender,  # Receiver of the asset
            asset_amount=quantity,  # Quantity to transfer
        ).submit()

    @arc4.abimethod(allow_actions=["DeleteApplication"])
    def delete_application(self) -> None:
        """
        Deletes the application, transferring remaining funds and assets to the creator.

        This method ensures a clean closure of the contract, freeing up resources.

        Validations:
            - Only the contract creator can delete the application.
        """
        # Ensure only the creator can delete the application
        assert Txn.sender == Global.creator_address

        # Transfer remaining assets to the creator
        itxn.AssetTransfer(
            xfer_asset=self.asset_id,  # Asset to transfer
            asset_receiver=Global.creator_address,  # Receiver is the creator
            asset_amount=0,  # Transfer zero to close interaction with the asset
            asset_close_to=Global.creator_address,  # Close asset interaction and send balance to the creator
        ).submit()

        # Transfer remaining Algo balance to the creator
        itxn.Payment(
            receiver=Global.creator_address,  # Receiver is the creator
            amount=0,  # Transfer zero Algo
            close_remainder_to=Global.creator_address,  # Send remaining balance to the creator
        ).submit()
