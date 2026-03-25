package com.terrarium.app.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * User's inventory - seeds, cuttings, decorations, etc.
 */
@Entity(tableName = "inventory")
data class InventoryItem(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val userId: Long,
    val itemId: Long, // References plant_type.id for seeds, or other item IDs
    val itemType: ItemType,
    val quantity: Int = 1,
    val acquiredAt: Long = System.currentTimeMillis()
)

/**
 * Types of inventory items.
 */
enum class ItemType {
    SEED,           // Plantable seeds
    CUTTING,        // Rooted cuttings (moved from Cuttings table when ready)
    DECORATION,    // Decorative items for terrariums
    JAR_UNLOCK,     // Unlocks a new jar type
    FERTILIZER,    // Boosts plant growth
    WATERING_CAN,   // Better watering tools
    PESTICIDE      // Protects plants from issues
}

/**
 * Shop item for purchasing.
 */
data class ShopItem(
    val id: Long,
    val name: String,
    val description: String,
    val itemType: ItemType,
    val price: Int,
    val emoji: String,
    val requiredLevel: Int = 1,
    val unlockAtLevel: Int? = null // Level at which this item becomes available
)

/**
 * Shop items by category.
 */
object ShopItems {
    val SEEDS = listOf(
        // Common seeds (always available)
        ShopItem(1, "Moss Seeds", "Grow soft green moss", ItemType.SEED, 10, "🌿", 1),
        ShopItem(2, "Fittonia Seeds", "Nerve plant seeds", ItemType.SEED, 10, "🌿", 1),
        ShopItem(3, "Air Plant Seeds", "No soil needed seeds", ItemType.SEED, 10, "🪴", 1),
        ShopItem(4, "Jade Plant Seeds", "Lucky succulent seeds", ItemType.SEED, 10, "🌵", 1),
        // Uncommon seeds (level 3+)
        ShopItem(5, "Fern Spores", "Classic terrarium fern", ItemType.SEED, 50, "🌿", 3),
        ShopItem(6, "Pilea Seeds", "Chinese money plant", ItemType.SEED, 50, "🌱", 3),
        ShopItem(7, "Peperomia Seeds", "Radiator plant seeds", ItemType.SEED, 50, "🌿", 3),
        ShopItem(8, "String of Pearls Seeds", "Cascading succulent", ItemType.SEED, 50, "📿", 3),
        // Rare seeds (level 7+)
        ShopItem(9, "Variegated Pilea Seeds", "Rare variegated variety", ItemType.SEED, 200, "✨", 7),
        ShopItem(10, "Pitcher Plant Seeds", "Carnivorous tropical seeds", ItemType.SEED, 200, "🌺", 7),
        ShopItem(11, "Venus Flytrap Seeds", "Snap! Carnivorous seeds", ItemType.SEED, 200, "🪤", 7),
        // Legendary seeds (level 12+)
        ShopItem(12, "Ghost Plant Seeds", "Ethereal white beauty", ItemType.SEED, 1000, "👻", 12),
        ShopItem(13, "Living Stones Seeds", "Stone-mimicking succulent", ItemType.SEED, 1000, "🪨", 12),
        ShopItem(14, "Marimo Seeds", "Aquatic moss sphere", ItemType.SEED, 1000, "🟢", 12),
        ShopItem(15, "Moon Orchid Seeds", "Mythical blue orchid", ItemType.SEED, 1000, "🌙", 12)
    )
    
    val JARS = listOf(
        ShopItem(101, "Small Jar", "Perfect for beginners. 3 plant capacity.", ItemType.JAR_UNLOCK, 0, "🏺", 1),
        ShopItem(102, "Medium Jar", "Standard-sized terrarium. 5 plant capacity.", ItemType.JAR_UNLOCK, 100, "🏺", 3),
        ShopItem(103, "Round Jar", "360° viewing angle. 4 plant capacity.", ItemType.JAR_UNLOCK, 150, "🔵", 7),
        ShopItem(104, "Tall Jar", "For taller plants. 6 plant capacity.", ItemType.JAR_UNLOCK, 200, "📐", 7),
        ShopItem(105, "Wide Jar", "Extra horizontal space. 7 plant capacity.", ItemType.JAR_UNLOCK, 250, "📦", 12)
    )
    
    val DECORATIONS = listOf(
        ShopItem(201, "Pebbles", "Decorative stones", ItemType.DECORATION, 25, "🪨", 1),
        ShopItem(202, "Miniature Bench", "Tiny garden bench", ItemType.DECORATION, 50, "🪑", 3),
        ShopItem(203, "Fairy House", "Cozy fairy dwelling", ItemType.DECORATION, 100, "🏠", 5),
        ShopItem(204, "Crystal Cluster", "Sparkly crystals", ItemType.DECORATION, 75, "💎", 5),
        ShopItem(205, "Mini Lake", "Tiny pond decoration", ItemType.DECORATION, 150, "🌊", 7)
    )
    
    val TOOLS = listOf(
        ShopItem(301, "Basic Fertilizer", "+20% growth speed", ItemType.FERTILIZER, 30, "🧪", 1),
        ShopItem(302, "Premium Fertilizer", "+50% growth speed", ItemType.FERTILIZER, 75, "⚗️", 5),
        ShopItem(303, "Pesticide", "Protects plants for 7 days", ItemType.PESTICIDE, 50, "🛡️", 3)
    )
    
    fun getAllItems(): List<ShopItem> = SEEDS + JARS + DECORATIONS + TOOLS
}