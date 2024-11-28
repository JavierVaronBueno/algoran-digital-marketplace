# Digitalmarketplace

A reusable Algorand ARC-4 compliant smart contract that implements a digital marketplace. This contract facilitates asset management, pricing, purchases, and fund withdrawal, making it an ideal choice for decentralized marketplaces.

## Features

- **Asset Management**: Opt-in to assets and manage their state.
- **Dynamic Pricing**: Set and update the unit price of an asset.
- **Asset Purchases**: Allow users to purchase assets through grouped transactions.
- **Secure Deletion**: Safely delete the application while transferring remaining assets and funds to the creator.

## Global State Variables

- `asset_id (UInt64)`: The ID of the asset managed by this contract.
- `unitary_price (UInt64)`: The unit price of the asset.

## Methods

### 1. `create_application(asset_id: Asset, unitary_price: UInt64)`

Initializes the smart contract.

#### Parameters:
- `asset_id`: The ID of the asset to manage.
- `unitary_price`: The unit price of the asset.

#### Notes:
- This method is called during the contract creation process.

---

### 2. `opt_in_to_asset(mbr_pay: gtxn.PaymentTransaction)`

Allows the smart contract to opt-in to the specified asset.

#### Parameters:
- `mbr_pay`: A payment transaction covering the opt-in cost.

#### Validations:
- Only the contract creator can call this method.
- The application must not already be opted-in to the asset.
- The receiver of the payment must be the application itself.
- The payment amount must meet minimum balance requirements.

---

### 3. `set_price(unitary_price: UInt64)`

Updates the unit price of the asset.

#### Parameters:
- `unitary_price`: The new unit price of the asset.

#### Validations:
- Only the contract creator can call this method.

---

### 4. `buy(quantity: UInt64, buyer_txn: gtxn.PaymentTransaction)`

Allows a user to purchase assets from the smart contract.

#### Parameters:
- `quantity`: The number of assets to purchase.
- `buyer_txn`: The payment transaction associated with the purchase.

#### Validations:
- The unit price must not be zero.
- The sender of the payment transaction must match the caller.
- The receiver of the payment must be the smart contract.
- The payment amount must equal the total cost of the purchase.

---

### 5. `delete_application()`

Deletes the application and transfers any remaining assets and funds to the contract creator.

#### Validations:
- Only the contract creator can call this method.

#### Notes:
- This method ensures a clean closure of the application and frees up resources.

---

## How to Use

1. **Deploy the Contract**: Call `create_application` with the desired `asset_id` and `unitary_price`.
2. **Opt-in to the Asset**: Use `opt_in_to_asset` to allow the contract to interact with the asset.
3. **Set the Price**: Adjust the unit price of the asset with `set_price`.
4. **Facilitate Purchases**: Allow buyers to call `buy` with their desired quantity.
5. **Clean Up**: When no longer needed, call `delete_application` to close the contract and transfer funds.

## Requirements

- Algorand blockchain and ARC-4 compliance.
- Adequate balance for minimum requirements when opting in to assets.
- Users must perform grouped transactions for certain operations, such as `buy`.

## License

This project is open-source and available under the [MIT License](LICENSE).

