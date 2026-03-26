package com.terrarium.app.data.model

/**
 * Represents a layer in the terrarium substrate.
 * Order matters: BOTTOM (gravel) → MIDDLE (charcoal) → TOP (soil)
 */
enum class LayerType {
    GRAVEL,      // Bottom layer - drainage
    CHARCOAL,    // Filter layer
    SOIL,        // Top layer - for planting
    MOSS,        // Decorative top layer
    DECORATION   // Optional decorative items
}

/**
 * A layer of material in the terrarium.
 */
data class TerrariumLayer(
    val type: LayerType,
    val depth: Float, // 0.0 to 1.0 (percentage of jar height)
    val color: String = when (type) {
        LayerType.GRAVEL -> "#8B7355"    // Brown/gray stones
        LayerType.CHARCOAL -> "#2C2C2C"  // Dark gray/black
        LayerType.SOIL -> "#4A3728"      // Dark brown
        LayerType.MOSS -> "#228B22"      // Forest green
        LayerType.DECORATION -> "#FFFFFF" // Varies by decoration
    }
)

/**
 * Visual position for a plant in the terrarium grid.
 * Coordinates are normalized 0-1.
 */
data class PlantPosition(
    val x: Float, // 0 = left, 1 = right
    val y: Float, // 0 = bottom (on soil), 1 = top
    val size: Float = 1.0f // Scale factor for plant size
) {
    /**
     * Convert to grid coordinates for collision detection.
     */
    fun toGridCell(gridSize: Int = 5): Pair<Int, Int> {
        val gridX = (x * gridSize).toInt().coerceIn(0, gridSize - 1)
        val gridY = (y * gridSize).toInt().coerceIn(0, gridSize - 1)
        return gridX to gridY
    }
}

/**
 * Base layers configuration for a terrarium.
 */
data class BaseLayerConfig(
    val hasGravel: Boolean = false,
    val hasCharcoal: Boolean = false,
    val hasSoil: Boolean = false,
    val hasMoss: Boolean = false
) {
    /**
     * Check if terrarium has all required layers for planting.
     */
    fun canPlant(): Boolean {
        return hasSoil // Minimum requirement is soil
    }
    
    /**
     * Get total depth of all layers (for visual rendering).
     */
    fun getTotalDepth(): Float {
        var depth = 0f
        if (hasGravel) depth += 0.1f
        if (hasCharcoal) depth += 0.05f
        if (hasSoil) depth += 0.15f
        if (hasMoss) depth += 0.05f
        return depth
    }
    
    /**
     * Get bonus XP for having complete layers.
     */
    fun getSetupBonus(): Int {
        var bonus = 0
        if (hasGravel) bonus += 5
        if (hasCharcoal) bonus += 10
        if (hasSoil) bonus += 15
        if (hasMoss) bonus += 10
        return bonus
    }
}