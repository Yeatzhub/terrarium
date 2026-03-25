package com.terrarium.app.data.repository

import com.terrarium.app.data.database.InventoryDao
import com.terrarium.app.data.model.InventoryItem
import com.terrarium.app.data.model.ItemType
import com.terrarium.app.data.model.ShopItems
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class InventoryRepository @Inject constructor(
    private val inventoryDao: InventoryDao
) {
    fun getInventoryForUser(userId: Long): Flow<List<InventoryItem>> = 
        inventoryDao.getInventoryForUser(userId)
    
    fun getInventoryByType(userId: Long, itemType: ItemType): Flow<List<InventoryItem>> = 
        inventoryDao.getInventoryByType(userId, itemType)
    
    fun getSeeds(userId: Long): Flow<List<InventoryItem>> = 
        inventoryDao.getInventoryByType(userId, ItemType.SEED)
    
    fun getCuttings(userId: Long): Flow<List<InventoryItem>> = 
        inventoryDao.getInventoryByType(userId, ItemType.CUTTING)
    
    suspend fun getInventoryItem(userId: Long, itemId: Long, itemType: ItemType): InventoryItem? = 
        inventoryDao.getInventoryItem(userId, itemId, itemType)
    
    suspend fun addInventoryItem(userId: Long, itemId: Long, itemType: ItemType, quantity: Int = 1) {
        val existing = inventoryDao.getInventoryItem(userId, itemId, itemType)
        if (existing != null) {
            inventoryDao.updateQuantity(userId, itemId, itemType, quantity)
        } else {
            inventoryDao.insertInventoryItem(
                InventoryItem(
                    userId = userId,
                    itemId = itemId,
                    itemType = itemType,
                    quantity = quantity
                )
            )
        }
    }
    
    suspend fun removeInventoryItem(userId: Long, itemId: Long, itemType: ItemType, quantity: Int = 1): Boolean {
        val existing = inventoryDao.getInventoryItem(userId, itemId, itemType)
        if (existing != null) {
            if (existing.quantity <= quantity) {
                inventoryDao.deleteInventoryItem(existing)
            } else {
                inventoryDao.updateQuantity(userId, itemId, itemType, -quantity)
            }
            return true
        }
        return false
    }
    
    suspend fun hasItem(userId: Long, itemId: Long, itemType: ItemType): Boolean {
        return inventoryDao.getInventoryItem(userId, itemId, itemType) != null
    }
    
    suspend fun getItemCount(userId: Long, itemId: Long, itemType: ItemType): Int {
        return inventoryDao.getInventoryItem(userId, itemId, itemType)?.quantity ?: 0
    }
    
    /**
     * Purchase an item from the shop.
     */
    suspend fun purchaseItem(userId: Long, shopItem: com.terrarium.app.data.model.ShopItem): PurchaseResult {
        // Add item to inventory
        addInventoryItem(userId, shopItem.id, shopItem.itemType)
        return PurchaseResult(success = true, message = "Purchased ${shopItem.name}")
    }
    
    /**
     * Get all inventory items with their details.
     */
    fun getInventoryWithDetails(userId: Long): Flow<List<InventoryItem>> {
        return getInventoryForUser(userId)
    }
}

/**
 * Result of a purchase attempt.
 */
data class PurchaseResult(
    val success: Boolean,
    val message: String,
    val itemId: Long? = null
)

/**
 * Inventory item with additional details.
 */
data class InventoryItemWithDetails(
    val item: InventoryItem,
    val name: String,
    val emoji: String,
    val description: String
)