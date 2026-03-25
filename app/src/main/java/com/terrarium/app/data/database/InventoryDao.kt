package com.terrarium.app.data.database

import androidx.room.*
import com.terrarium.app.data.model.InventoryItem
import com.terrarium.app.data.model.ItemType
import kotlinx.coroutines.flow.Flow

@Dao
interface InventoryDao {
    @Query("SELECT * FROM inventory WHERE userId = :userId ORDER BY itemType, itemId")
    fun getInventoryForUser(userId: Long): Flow<List<InventoryItem>>
    
    @Query("SELECT * FROM inventory WHERE userId = :userId AND itemType = :itemType")
    fun getInventoryByType(userId: Long, itemType: ItemType): Flow<List<InventoryItem>>
    
    @Query("SELECT * FROM inventory WHERE userId = :userId AND itemId = :itemId AND itemType = :itemType")
    suspend fun getInventoryItem(userId: Long, itemId: Long, itemType: ItemType): InventoryItem?
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertInventoryItem(item: InventoryItem): Long
    
    @Update
    suspend fun updateInventoryItem(item: InventoryItem)
    
    @Delete
    suspend fun deleteInventoryItem(item: InventoryItem)
    
    @Query("UPDATE inventory SET quantity = quantity + :amount WHERE userId = :userId AND itemId = :itemId AND itemType = :itemType")
    suspend fun updateQuantity(userId: Long, itemId: Long, itemType: ItemType, amount: Int)
}