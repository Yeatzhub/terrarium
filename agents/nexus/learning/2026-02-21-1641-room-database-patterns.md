# 📱 Room Database: Advanced Patterns

**Focus:** FTS Search, Migrations, Relations, Type Converters, Performance
**Pattern:** Multi-table design with offline search + data integrity

---

## 1. Entity Design

```kotlin
@Entity(tableName = "assets")
data class AssetEntity(
    @PrimaryKey val id: String,
    val symbol: String,
    val name: String,
    @ColumnInfo(name = "market_cap") val marketCap: Long?,
    @ColumnInfo(name = "created_at") val createdAt: Long = System.currentTimeMillis(),
    @ColumnInfo(defaultValue = "false") val isFavorite: Boolean = false
)

@Entity(
    tableName = "prices",
    indices = [
        Index(value = ["asset_id"]),
        Index(value = ["timestamp"])
    ],
    foreignKeys = [
        ForeignKey(
            entity = AssetEntity::class,
            parentColumns = ["id"],
            childColumns = ["asset_id"],
            onDelete = ForeignKey.CASCADE
        )
    ]
)
data class PriceEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    @ColumnInfo(name = "asset_id") val assetId: String,
    val price: String, // BigDecimal as String
    val volume: Double,
    val timestamp: Long,
    @ColumnInfo(name = "price_change_24h") val priceChange24h: String?
)

// FTS Virtual Table for search
@Fts4(contentEntity = AssetEntity::class)
@Entity(tableName = "assets_fts")
data class AssetFtsEntity(
    val symbol: String,
    val name: String
)

// Embedded value object
@Embedded
data class PriceChange(
    val percent: Double,
    val amount: String,
    @ColumnInfo(name = "change_direction") val direction: ChangeDirection
)

enum class ChangeDirection { UP, DOWN, NEUTRAL }
```

---

## 2. DAO Patterns

```kotlin
@Dao
interface AssetDao {
    // Basic CRUD
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(asset: AssetEntity)
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(assets: List<AssetEntity>)
    
    @Update
    suspend fun update(asset: AssetEntity)
    
    @Delete
    suspend fun delete(asset: AssetEntity)
    
    // Flow queries (reactive)
    @Query("SELECT * FROM assets ORDER BY market_cap DESC")
    fun observeAll(): Flow<List<AssetEntity>>
    
    @Query("SELECT * FROM assets WHERE isFavorite = 1")
    fun observeFavorites(): Flow<List<AssetEntity>>
    
    // FTS search
    @Transaction
    @Query("""
        SELECT assets.* FROM assets_fts 
        JOIN assets ON assets_fts.rowid = assets.id 
        WHERE assets_fts MATCH :query
    """)
    fun searchAssets(query: String): Flow<List<AssetEntity>>
    
    // Paging support
    @Query("SELECT * FROM assets ORDER BY market_cap DESC LIMIT :limit OFFSET :offset")
    suspend fun getPage(limit: Int, offset: Int): List<AssetEntity>
    
    @Query("SELECT COUNT(*) FROM assets")
    suspend fun getCount(): Int
    
    // Complex aggregations
    @Query("""
        SELECT COUNT(DISTINCT asset_id) as assetCount,
               COUNT(*) as pricePointCount,
               MIN(timestamp) as oldestData
        FROM prices
        WHERE timestamp > :since
    """)
    suspend fun getStatistics(since: Long = 0): PriceStatistics
}

@Dao
interface PriceDao {
    @Insert
    suspend fun insert(price: PriceEntity)
    
    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertAll(prices: List<PriceEntity>): List<Long>
    
    // One-to-Many query with relation
    @Transaction
    @Query("SELECT * FROM assets WHERE id = :assetId")
    suspend fun getAssetWithPrices(assetId: String): AssetWithPrices?
    
    // Time-series query
    @Query("""
        SELECT * FROM prices 
        WHERE asset_id = :assetId 
        AND timestamp BETWEEN :startTime AND :endTime
        ORDER BY timestamp DESC
    """)
    fun getPriceHistory(
        assetId: String,
        startTime: Long,
        endTime: Long = System.currentTimeMillis()
    ): Flow<List<PriceEntity>>
    
    // Bulk delete with date range
    @Query("DELETE FROM prices WHERE timestamp < :olderThan")
    suspend fun deleteOlderThan(olderThan: Long)
    
    // Upsert using SQLite ON CONFLICT
    @Query("""
        INSERT INTO prices (asset_id, price, volume, timestamp, price_change_24h)
        VALUES (:assetId, :price, :volume, :timestamp, :change24h)
        ON CONFLICT(timestamp) DO UPDATE SET
            price = excluded.price,
            volume = excluded.volume,
            price_change_24h = excluded.price_change_24h
    """)
    suspend fun upsert(
        assetId: String,
        price: String,
        volume: Double,
        timestamp: Long,
        change24h: String?
    )
}

// Relation data class
@Dao
interface PortfolioDao {
    // Many-to-Many with cross-ref table
    @Transaction
    @Query("SELECT * FROM portfolios WHERE id = :portfolioId")
    suspend fun getPortfolioWithAssets(portfolioId: String): PortfolioWithAssets?
    
    @Insert
    suspend fun addAssetToPortfolio(crossRef: PortfolioAssetCrossRef)
}

data class PortfolioWithAssets(
    @Embedded val portfolio: PortfolioEntity,
    @Relation(
        parentColumn = "id",
        entityColumn = "id",
        associateBy = Junction(PortfolioAssetCrossRef::class)
    )
    val assets: List<AssetEntity>
)

data class AssetWithPrices(
    @Embedded val asset: AssetEntity,
    @Relation(
        parentColumn = "id",
        entityColumn = "asset_id"
    )
    val prices: List<PriceEntity>
)
```

---

## 3. Type Converters

```kotlin
class RoomTypeConverters {
    // DateTime handling
    @TypeConverter
    fun fromInstant(value: java.time.Instant?): Long? = value?.toEpochMilli()
    
    @TypeConverter
    fun toInstant(value: Long?): java.time.Instant? = 
        value?.let { java.time.Instant.ofEpochMilli(it) }
    
    // BigDecimal precision
    @TypeConverter
    fun fromBigDecimal(value: BigDecimal?): String? = value?.toPlainString()
    
    @TypeConverter
    fun toBigDecimal(value: String?): BigDecimal? = 
        value?.let { BigDecimal(it) }
    
    // Enum storage (compact)
    @TypeConverter
    fun fromChangeDirection(direction: ChangeDirection?): String? = 
        direction?.name
    
    @TypeConverter
    fun toChangeDirection(value: String?): ChangeDirection? = 
        value?.let { ChangeDirection.valueOf(it) }
    
    // JSON storage for flexible data
    @TypeConverter
    fun fromMetadata(metadata: Map<String, Any>?): String? = 
        metadata?.let { Gson().toJson(it) }
    
    @TypeConverter
    fun toMetadata(json: String?): Map<String, Any>? = 
        json?.let { 
            Gson().fromJson(it, object : TypeToken<Map<String, Any>>() {}.type) 
        }
    
    // List storage
    @TypeConverter
    fun fromStringList(value: List<String>?): String? = 
        value?.joinToString(",")
    
    @TypeConverter
    fun toStringList(value: String?): List<String> = 
        value?.split(",") ?: emptyList()
}
```

---

## 4. Database Configuration

```kotlin
@Database(
    entities = [
        AssetEntity::class,
        PriceEntity::class,
        AssetFtsEntity::class,
        PortfolioEntity::class,
        PortfolioAssetCrossRef::class
    ],
    version = 5,
    exportSchema = true // Enable for migrations
)
@TypeConverters(RoomTypeConverters::class)
abstract class TradingDatabase : RoomDatabase() {
    abstract fun assetDao(): AssetDao
    abstract fun priceDao(): PriceDao
    abstract fun portfolioDao(): PortfolioDao
}

// Module configuration
@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {
    
    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): TradingDatabase {
        return Room.databaseBuilder(
            context,
            TradingDatabase::class.java,
            "trading.db"
        )
        // Migration strategy
        .addMigrations(MIGRATION_1_2, MIGRATION_2_3, MIGRATION_3_4, MIGRATION_4_5)
        // Callbacks
        .addCallback(object : RoomDatabase.Callback() {
            override fun onCreate(db: SupportSQLiteDatabase) {
                super.onCreate(db)
                // Populate initial FTS data
                db.execSQL("""
                    INSERT INTO assets_fts(assets_fts) VALUES('rebuild')
                """)
            }
        })
        // Performance tuning
        .setQueryCallback({ sqlQuery, bindArgs ->
            if (BuildConfig.DEBUG) {
                Log.d("RoomQuery", "SQL: $sqlQuery | Args: $bindArgs")
            }
        }, Executors.newSingleThreadExecutor())
        .build()
    }
}

// Migration definitions
val MIGRATION_1_2 = object : Migration(1, 2) {
    override fun migrate(database: SupportSQLiteDatabase) {
        database.execSQL("""
            ALTER TABLE assets ADD COLUMN isFavorite INTEGER NOT NULL DEFAULT 0
        """)
    }
}

val MIGRATION_2_3 = object : Migration(2, 3) {
    override fun migrate(database: SupportSQLiteDatabase) {
        // Create FTS table
        database.execSQL("""
            CREATE VIRTUAL TABLE IF NOT EXISTS assets_fts USING fts4(
                symbol TEXT, 
                name TEXT, 
                content=assets
            )
        """)
    }
}

val MIGRATION_3_4 = object : Migration(3, 4) {
    override fun migrate(database: SupportSQLiteDatabase) {
        database.execSQL("""
            CREATE TABLE IF NOT EXISTS portfolios (
                id TEXT PRIMARY KEY NOT NULL,
                name TEXT NOT NULL,
                created_at INTEGER NOT NULL
            )
        """)
        database.execSQL("""
            CREATE TABLE IF NOT EXISTS portfolio_asset_cross_ref (
                portfolioId TEXT NOT NULL,
                assetId TEXT NOT NULL,
                PRIMARY KEY(portfolioId, assetId),
                FOREIGN KEY(portfolioId) REFERENCES portfolios(id) ON DELETE CASCADE,
                FOREIGN KEY(assetId) REFERENCES assets(id) ON DELETE CASCADE
            )
        """)
    }
}

val MIGRATION_4_5 = object : Migration(4, 5) {
    override fun migrate(database: SupportSQLiteDatabase) {
        // Rename and recreate with new constraints
        database.execSQL("""
            CREATE TABLE prices_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                asset_id TEXT NOT NULL,
                price TEXT NOT NULL,
                volume REAL NOT NULL,
                timestamp INTEGER NOT NULL,
                price_change_24h TEXT,
                FOREIGN KEY(asset_id) REFERENCES assets(id) ON DELETE CASCADE
            )
        """)
        database.execSQL("""
            INSERT INTO prices_new SELECT * FROM prices
        """)
        database.execSQL("DROP TABLE prices")
        database.execSQL("ALTER TABLE prices_new RENAME TO prices")
        database.execSQL("CREATE INDEX idx_prices_asset ON prices(asset_id)")
        database.execSQL("CREATE INDEX idx_prices_time ON prices(timestamp)")
    }
}
```

---

## 5. Repository Integration

```kotlin
@Singleton
class AssetRepository @Inject constructor(
    private val db: TradingDatabase,
    private val api: TradingApi,
    @IoDispatcher private val ioDispatcher: CoroutineDispatcher
) {
    private val assetDao = db.assetDao()
    private val priceDao = db.priceDao()
    
    // Offline-first search with FTS
    fun searchAssets(query: String): Flow<List<Asset>> = 
        if (query.isBlank()) {
            assetDao.observeAll()
        } else {
            // Room FTS supports prefix matching
            assetDao.searchAssets("$query*")
        }
        .map { list -> list.map { it.toDomain() } }
        .flowOn(ioDispatcher)
    
    // Time-series with caching
    fun getPriceHistory(
        assetId: String,
        timeframe: TimeFrame
    ): Flow<List<Price>> = flow {
        // Check cache freshness
        val cachedCount = priceDao.getCountForTimeframe(assetId, timeframe)
        
        if (cachedCount < timeframe.minDataPoints) {
            // Fetch from API
            emit(Resource.Loading)
            try {
                val remoteData = api.getPriceHistory(assetId, timeframe)
                priceDao.insertAll(remoteData.map { it.toEntity() })
            } catch (e: Exception) {
                // Continue with cached data on error
            }
        }
        
        // Emit from database
        priceDao.getPriceHistory(assetId, timeframe.startTime)
            .map { it.map { p -> p.toDomain() } }
            .map { Resource.Success(it) }
            .collect { emit(it) }
    }.flowOn(ioDispatcher)
    
    // Transactional operations
    suspend fun toggleFavorite(assetId: String) {
        withContext(ioDispatcher) {
            db.withTransaction {
                val asset = assetDao.getById(assetId)
                    ?: throw IllegalStateException("Asset not found")
                assetDao.update(asset.copy(isFavorite = !asset.isFavorite))
            }
        }
    }
    
    // Bulk operations with progress
    suspend fun syncAssets(onProgress: (Int, Int) -> Unit) {
        withContext(ioDispatcher) {
            val remoteAssets = api.getTopAssets(500)
            val total = remoteAssets.size
            
            remoteAssets.chunked(50).forEachIndexed { index, chunk ->
                assetDao.insertAll(chunk.map { it.toEntity() })
                onProgress((index + 1) * 50, total)
            }
        }
    }
    
    // Database maintenance
    suspend fun cleanupOldData(keepDays: Int = 30) {
        withContext(ioDispatcher) {
            val cutoff = System.currentTimeMillis() - (keepDays * 24 * 60 * 60 * 1000)
            priceDao.deleteOlderThan(cutoff)
            db.query(SimpleSQLiteQuery("VACUUM")) // Reclaim space
        }
    }
}
```

---

## 6. Performance Best Practices

```kotlin
// ✅ DO: Use @Transaction for related queries
@Transaction
@Query("SELECT * FROM assets WHERE id = :id")
suspend fun getAssetWithPrices(id: String): AssetWithPrices

// ✅ DO: Use indices on foreign keys and query columns
@Entity(
    tableName = "prices",
    indices = [
        Index("asset_id"), // Foreign key needs index
        Index(value = ["timestamp", "asset_id"]) // Composite for queries
    ]
)

// ✅ DO: Flow for reactive queries
@Query("SELECT * FROM assets WHERE isFavorite = 1")
fun observeFavorites(): Flow<List<AssetEntity>> // Auto-updates

// ✅ DO: Batch inserts
@Insert
suspend fun insertAll(assets: List<AssetEntity>) // Single transaction

// ✅ DO: Use upsert for idempotent writes
@Query("""
    INSERT INTO ... ON CONFLICT(...) DO UPDATE SET ...
""")

// ❌ DON'T: Query on main thread
// Bad: dao.getAll() called without coroutines
// Good: withContext(ioDispatcher) { dao.getAll() }

// ❌ DON'T: Return mutable collections
// Return immutable List, not ArrayList

// ❌ DON'T: Store large blobs in entities
// Store file path, not file contents
```

---

## 7. Testing

```kotlin
@RunWith(AndroidJUnit4::class)
class DatabaseTest {
    private lateinit var db: TradingDatabase
    private lateinit var assetDao: AssetDao
    private lateinit var priceDao: PriceDao
    
    @Before
    fun setup() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        db = Room.inMemoryDatabaseBuilder(context, TradingDatabase::class.java)
            .allowMainThreadQueries()
            .build()
        assetDao = db.assetDao()
        priceDao = db.priceDao()
    }
    
    @After
    fun teardown() {
        db.close()
    }
    
    @Test
    fun insertAndReadAsset() = runTest {
        val asset = AssetEntity("btc", "BTC", "Bitcoin", 800000000000, isFavorite = true)
        assetDao.insert(asset)
        
        val result = assetDao.observeFavorites().first()
        
        assertEquals(1, result.size)
        assertEquals("BTC", result[0].symbol)
    }
    
    @Test
    fun cascadeDeleteWorks() = runTest {
        val asset = AssetEntity("btc", "BTC", "Bitcoin", 1000000000000)
        assetDao.insert(asset)
        
        val price = PriceEntity(0, "btc", "50000", 1000.0, System.currentTimeMillis(), null)
        priceDao.insert(price)
        
        // Verify price exists
        val beforeDelete = priceDao.getPriceHistory("btc", 0).first()
        assertEquals(1, beforeDelete.size)
        
        // Delete asset
        assetDao.delete(asset)
        
        // Verify cascading delete
        val afterDelete = priceDao.getPriceHistory("btc", 0).first()
        assertTrue(afterDelete.isEmpty())
    }
    
    @Test
    fun ftsSearchWorks() = runTest {
        val bitcoin = AssetEntity("btc", "BTC", "Bitcoin", 800000000000)
        val ethereum = AssetEntity("eth", "ETH", "Ethereum", 200000000000)
        assetDao.insertAll(listOf(bitcoin, ethereum))
        
        // Rebuild FTS index
        db.query(SimpleSQLiteQuery("INSERT INTO assets_fts(assets_fts) VALUES('rebuild')"))
        
        val results = assetDao.searchAssets("bit*").first()
        
        assertEquals(1, results.size)
        assertEquals("Bitcoin", results[0].name)
    }
    
    @Test
    fun migrationTest() {
        // Create database at version 4
        val db = Room.inMemoryDatabaseBuilder(
            ApplicationProvider.getApplicationContext(),
            TradingDatabase::class.java
        )
        .addMigrations(MIGRATION_4_5)
        .build()
        
        // Insert old format data
        db.openHelper.writableDatabase.execSQL(
            "INSERT INTO prices (asset_id, price, volume, timestamp) VALUES ('btc', '50000', 1000.0, 123456)"
        )
        
        // Verify migration preserved data
        val cursor = db.query(SimpleSQLiteQuery("SELECT * FROM prices"))
        assertTrue(cursor.moveToFirst())
        assertEquals("btc", cursor.getString(cursor.getColumnIndexOrThrow("asset_id")))
    }
}
```

---

## TL;DR

| Pattern | Implementation |
|---------|----------------|
| **FTS Search** | `@Fts4` virtual table + JOIN queries |
| **Relations** | `@Embedded` + `@Relation` for 1:N, `@Junction` for N:M |
| **Type Safety** | `@TypeConverter` for enums, dates, BigDecimal |
| **Migrations** | `Migration(old, new)` + incremental versions |
| **Performance** | Indices on FKs, `@Transaction`, bulk inserts |
| **Reactive** | `Flow` return types for auto updates |
| **Integrity** | Foreign key constraints + cascading deletes |

**Remember:** Room validates SQL at compile time, uses FTS for search, and Flow for reactive updates. Always use `withTransaction` for multi-table operations.
