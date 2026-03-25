package com.terrarium.app.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Predefined plant types with their characteristics.
 * This is a reference table, not user data.
 */
@Entity(tableName = "plant_types")
data class PlantType(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val name: String,
    val scientificName: String,
    val tier: RarityTier,
    val growthTimeHours: Int,
    val minMoisture: Float,
    val maxMoisture: Float,
    val minLight: Float,
    val maxLight: Float,
    val description: String = "",
    val emoji: String = "🌱"
)

/**
 * Plant rarity tiers.
 */
enum class RarityTier {
    COMMON,
    UNCOMMON,
    RARE,
    LEGENDARY
}

/**
 * Default plant types available in the game.
 */
object DefaultPlantTypes {
    val ALL = listOf(
        // Common plants (4-8 hours)
        PlantType(1, "Moss", "Bryophyta", RarityTier.COMMON, 4, 0.6f, 0.9f, 0.2f, 0.6f, "Soft and green", "🌿"),
        PlantType(2, "Fittonia", "Fittonia albivenis", RarityTier.COMMON, 5, 0.5f, 0.8f, 0.2f, 0.5f, "Nerve plant with colorful veins", "🌿"),
        PlantType(3, "Air Plant", "Tillandsia", RarityTier.COMMON, 6, 0.3f, 0.5f, 0.5f, 1.0f, "No soil needed", "🪴"),
        PlantType(4, "Jade Plant", "Crassula ovata", RarityTier.COMMON, 8, 0.3f, 0.6f, 0.3f, 0.7f, "Lucky succulent", "🌵"),
        
        // Uncommon plants (1-2 days)
        PlantType(5, "Fern", "Pteridophyta", RarityTier.UNCOMMON, 24, 0.6f, 0.9f, 0.2f, 0.5f, "Classic terrarium plant", "🌿"),
        PlantType(6, "Pilea", "Pilea peperomioides", RarityTier.UNCOMMON, 36, 0.4f, 0.7f, 0.3f, 0.6f, "Chinese money plant", "🌱"),
        PlantType(7, "Peperomia", "Peperomia", RarityTier.UNCOMMON, 36, 0.4f, 0.7f, 0.2f, 0.5f, "Radiator plant", "🌿"),
        PlantType(8, "String of Pearls", "Senecio rowleyanus", RarityTier.UNCOMMON, 48, 0.2f, 0.4f, 0.4f, 0.8f, "Cascading beauty", "📿"),
        
        // Rare plants (3-5 days)
        PlantType(9, "Variegated Pilea", "Pilea peperomioides variegata", RarityTier.RARE, 72, 0.4f, 0.7f, 0.3f, 0.6f, "Rare variegated variety", "✨"),
        PlantType(10, "Pitcher Plant", "Nepenthes", RarityTier.RARE, 96, 0.7f, 0.9f, 0.5f, 0.8f, "Carnivorous tropical", "🌺"),
        PlantType(11, "Venus Flytrap", "Dionaea muscipula", RarityTier.RARE, 120, 0.6f, 0.8f, 0.6f, 1.0f, "Snap! Carnivorous", "🪤"),
        
        // Legendary plants (7-14 days)
        PlantType(12, "Ghost Plant", "Monotropa uniflora", RarityTier.LEGENDARY, 168, 0.7f, 0.9f, 0.1f, 0.3f, "Ethereal white beauty", "👻"),
        PlantType(13, "Living Stones", "Lithops", RarityTier.LEGENDARY, 240, 0.1f, 0.3f, 0.6f, 1.0f, "Stone-mimicking succulent", "🪨"),
        PlantType(14, "Marimo Moss Ball", "Aegagropila linnaei", RarityTier.LEGENDARY, 336, 0.8f, 1.0f, 0.1f, 0.4f, "Aquatic moss sphere", "🟢"),
        PlantType(15, "Moon Orchid", "Phalaenopsis blue", RarityTier.LEGENDARY, 336, 0.5f, 0.7f, 0.3f, 0.5f, "Mythical blue orchid", "🌙")
    )
}