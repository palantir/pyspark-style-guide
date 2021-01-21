# PySpark Style Guide

PySpark is a wrapper language that allows users to interface with an Apache Spark backend to quickly process data. Spark can operate on massive datasets across a distributed network of servers, providing major performance and reliability benefits when utilized correctly. It presents challenges, even for experienced Python developers, as the PySpark syntax draws on the JVM heritage of Spark and therefore implements code patterns that may be unfamiliar.

This opinionated guide to PySpark code style presents common situations we've encountered and the associated best practices based on the most frequent recurring topics across PySpark repos.

Beyond PySpark specifics, the general practices of clean code are important in PySpark repositories- the Google [PyGuide](https://github.com/google/styleguide/blob/gh-pages/pyguide.md) is a strong starting point for learning more about these practices.



# Prefer implicit column selection to direct access, except for disambiguation

```python
# bad
df = df.select(F.lower(df1.colA), F.upper(df2.colB))

# good
df = df.select(F.lower(F.col('colA')), F.upper(F.col('colB')))

# better - since Spark 3.0
df = df.select(F.lower('colA'), F.upper('colB'))
```

In most situations, it's best to avoid the first and second styles and just reference the column by its name, using a string, as in the third example. Spark 3.0 [greatly expanded](https://issues.apache.org/jira/browse/SPARK-26979) the cases where this works. When the string method is not possible, however, we must resort to a more verbose approach.

In many situations the first style can be simpler, shorter and visually less polluted. However, we have found that it faces a number of limitations, that lead us to prefer the second style:

- If the dataframe variable name is large, expressions involving it quickly become unwieldy;
- If the column name has a space or other unsupported character, the bracket operator must be used instead. This generates inconsistency, and `df1['colA']` is just as difficult to write as `F.col('colA')`;
- Column expressions involving the dataframe aren't reusable and can't be used for defining abstract functions;
- Renaming a dataframe variable can be error-prone, as all column references must be updated in tandem.

Additionally, the dot syntax encourages use of short and non-descriptive variable names for the dataframes, which we have found to be harmful for maintainability. Remember that dataframes are containers for data, and descriptive names is a helpful way to quickly set expectations about what's contained within. 

By contrast, `F.col('colA')` will always reference a column designated `colA` in the dataframe being operated on, named `df`, in this case. It does not require keeping track of other dataframes' states at all, so the code becomes more local and less susceptible to "spooky interaction at a distance," which is often challenging to debug.

### Caveats

In some contexts there may be access to columns from more than one dataframe, and there may be an overlap in names. A common example is in matching expressions like `df.join(df2, on=(df.key == df2.key), how='left')`. In such cases it is fine to reference columns by their dataframe directly. You can also disambiguate joins using dataframe aliases (see more in the **Joins** section in this guide).


# Refactor complex logical operations

Logical operations, which often reside inside `.filter()` or `F.when()`, need to be readable. We apply the same rule as with chaining functions, keeping logic expressions inside the same code block to *three (3) expressions at most*. If they grow longer, it is often a sign that the code can be simplified or extracted out. Extracting out complex logical operations into variables makes the code easier to read and reason about, which also reduces bugs.

```python
# bad
F.when( (F.col('prod_status') == 'Delivered') | (((F.datediff('deliveryDate_actual', 'current_date') < 0) & ((F.col('currentRegistration') != '') | ((F.datediff('deliveryDate_actual', 'current_date') < 0) & ((F.col('originalOperator') != '') | (F.col('currentOperator') != '')))))), 'In Service')
```

The code above can be simplified in different ways. To start, focus on grouping the logic steps in a few named variables. PySpark requires that expressions are wrapped with parentheses. This, mixed with actual parenthesis to group logical operations, can hurt readability. For example the code above has a redundant `(F.datediff(df.deliveryDate_actual, df.current_date) < 0)` that the original author didn't notice because it's very hard to spot.

```python
# better
has_operator = ((F.col('originalOperator') != '') | (F.col('currentOperator') != ''))
delivery_date_passed = (F.datediff('deliveryDate_actual', 'current_date') < 0)
has_registration = (F.col('currentRegistration').rlike('.+'))
is_delivered = (F.col('prod_status') == 'Delivered')

F.when(is_delivered | (delivery_date_passed & (has_registration | has_operator)), 'In Service')
```

The above example drops the redundant expression and is easier to read. We can improve it further by reducing the number of operations.

```python
# good
has_operator = ((F.col('originalOperator') != '') | (F.col('currentOperator') != ''))
delivery_date_passed = (F.datediff('deliveryDate_actual', 'current_date') < 0)
has_registration = (F.col('currentRegistration').rlike('.+'))
is_delivered = (F.col('prod_status') == 'Delivered')
is_active = (has_registration | has_operator)

F.when(is_delivered | (delivery_date_passed & is_active), 'In Service')
```

Note how the `F.when` expression is now succinct and readable and the desired behavior is clear to anyone reviewing this code. The reader only needs to visit the individual expressions if they suspect there is an error. It also makes each chunk of logic easy to test if you have unit tests in your code, and want to abstract them as functions.

There is still some duplication of code in the final example: how to remove that duplication is an exercise for the reader.


# Use `select` statements to specify a schema contract

Doing a select at the beginning of a PySpark transform, or before returning, is considered good practice. This `select` statement specifies the contract with both the reader and the code about the expected dataframe schema for inputs and outputs. Any select should be seen as a cleaning operation that is preparing the dataframe for consumption by the next step in the transform.

Keep select statements as simple as possible. Due to common SQL idioms, allow only *one* function from `spark.sql.function` to be used per selected column, plus an optional `.alias()` to give it a meaningful name. Keep in mind that this should be used sparingly. If there are more than *three* such uses in the same select, refactor it into a separate function like `clean_<dataframe name>()` to encapsulate the operation.

Expressions involving more than one dataframe, or conditional operations like `.when()` are discouraged to be used in a select, unless required for performance reasons.


```python
# bad
aircraft = aircraft.select(
    'aircraft_id',
    'aircraft_msn',
    F.col('aircraft_registration').alias('registration'),
    'aircraft_type',
    F.avg('staleness').alias('avg_staleness'),
    F.col('number_of_economy_seats').cast('long'),
    F.avg('flight_hours').alias('avg_flight_hours'),
    'operator_code',
    F.col('number_of_business_seats').cast('long'),
)
```

Unless order matters to you, try to cluster together operations of the same type.

```python
# good
aircraft = aircraft.select(
    'aircraft_id',
    'aircraft_msn',
    'aircraft_type',
    'operator_code',
    F.col('aircraft_registration').alias('registration'),
    F.col('number_of_economy_seats').cast('long'),
    F.col('number_of_business_seats').cast('long'),
    F.avg('staleness').alias('avg_staleness'),
    F.avg('flight_hours').alias('avg_flight_hours'),
)
```

The `select()` statement redefines the schema of a dataframe, so it naturally supports the inclusion or exclusion of columns, old and new, as well as the redefinition of pre-existing ones. By centralising all such operations in a single statement, it becomes much easier to identify the final schema, which makes code more readable. It also makes code more concise.

Instead of calling `withColumnRenamed()`, use aliases:


```python
#bad
df.select('key', 'comments').withColumnRenamed('comments', 'num_comments')

# good
df.select('key', F.col('comments').alias('num_comments'))
```

Instead of using `withColumn()` to redefine type, cast in the select:
```python
# bad
df.select('comments').withColumn('comments', F.col('comments').cast('double'))

# good
df.select(F.col('comments').cast('double'))
```

But keep it simple:
```python
# bad
df.select(
    ((F.coalesce(F.unix_timestamp('closed_at'), F.unix_timestamp())
    - F.unix_timestamp('created_at')) / 86400).alias('days_open')
)

# good
df.withColumn(
    'days_open',
    (F.coalesce(F.unix_timestamp('closed_at'), F.unix_timestamp()) - F.unix_timestamp('created_at')) / 86400
)
```

Avoid including columns in the select statement if they are going to remain unused and choose instead an explicit set of columns - this is a preferred alternative to using `.drop()` since it guarantees that schema mutations won't cause unexpected columns to bloat your dataframe. However, dropping columns isn't inherintly discouraged in all cases; for instance- it is commonly appropriate to drop columns after joins since it is common for joins to introduce redundant columns. 

Finally, instead of adding new columns via the select statement, using `.withColumn()` is recommended instead for single columns. When adding or manipulating tens or hundreds of columns, use a single `.select()` for performance reasons.

# Empty columns

If you need to add an empty column to satisfy a schema, always use `F.lit(None)` for populating that column. Never use an empty string or some other string signalling an empty value (such as `NA`).

Beyond being semantically correct, one practical reason for using `F.lit(None)` is preserving the ability to use utilities like `isNull`, instead of having to verify empty strings, nulls, and `'NA'`, etc.


```python
# bad
df = df.withColumn('foo', F.lit(''))

# bad
df = df.withColumn('foo', F.lit('NA'))

# good
df = df.withColumn('foo', F.lit(None))
```

# Using comments

While comments can provide useful insight into code, it is often more valuable to refactor the code to improve its readability. The code should be readable by itself. If you are using comments to explain the logic step by step, you should refactor it.

```python
# bad

# Cast the timestamp columns
cols = ['start_date', 'delivery_date']
for c in cols:
    df = df.withColumn(c, F.from_unixtime(F.col(c) / 1000).cast(TimestampType()))
```

In the example above, we can see that those columns are getting cast to Timestamp. The comment doesn't add much value. Moreover, a more verbose comment might still be unhelpful if it only
provides information that already exists in the code. For example:

```python
# bad

# Go through each column, divide by 1000 because millis and cast to timestamp
cols = ['start_date', 'delivery_date']
for c in cols:
    df = df.withColumn(c, F.from_unixtime(F.col(c) / 1000).cast(TimestampType()))
```

Instead of leaving comments that only describe the logic you wrote, aim to leave comments that give context, that explain the "*why*" of decisions you made when writing the code. This is particularly important for PySpark, since the reader can understand your code, but often doesn't have context on the data that feeds into your PySpark transform. Small pieces of logic might have involved hours of digging through data to understand the correct behavior, in which case comments explaining the rationale are especially valuable.

```python
# good

# The consumer of this dataset expects a timestamp instead of a date, and we need
# to adjust the time by 1000 because the original datasource is storing these as millis
# even though the documentation says it's actually a date.
cols = ['start_date', 'delivery_date']
for c in cols:
    df = df.withColumn(c, F.from_unixtime(F.col(c) / 1000).cast(TimestampType()))
```

# UDFs (user defined functions)

It is highly recommended to avoid UDFs in all situations, as they are dramatically less performant than native PySpark. In most situations, logic that seems to necessitate a UDF can be refactored to use only native PySpark functions.

# Joins

Be careful with joins! If you perform a left join, and the right side has multiple matches for a key, that row will be duplicated as many times as there are matches. This is called a "join explosion" and can dramatically bloat the output of your transforms job. Always double check your assumptions to see that the key you are joining on is unique, unless you are expecting the multiplication.

Bad joins are the source of many tricky-to-debug issues. There are some things that help like specifying the `how` explicitly, even if you are using the default value `(inner)`:


```python
# bad
flights = flights.join(aircraft, 'aircraft_id')

# also bad
flights = flights.join(aircraft, 'aircraft_id', 'inner')

# good
flights = flights.join(aircraft, 'aircraft_id', how='inner')
```

Avoid `right` joins. If you are about to use a `right` join, switch the order of your dataframes and use a `left` join instead. It is more intuitive since the dataframe you are doing the operation on is the one that you are centering your join around.

```python
# bad
flights = aircraft.join(flights, 'aircraft_id', how='right')

# good
flights = flights.join(aircraft, 'aircraft_id', how='left')
```

Avoid renaming all columns to avoid collisions. Instead, give an alias to the
whole dataframe, and use that alias to select which columns you want in the end.

```python
# bad
columns = ['start_time', 'end_time', 'idle_time', 'total_time']
for col in columns:
    flights = flights.withColumnRenamed(col, 'flights_' + col)
    parking = parking.withColumnRenamed(col, 'parking_' + col)

flights = flights.join(parking, on='flight_code', how='left')

flights = flights.select(
    F.col('flights_start_time').alias('flight_start_time'),
    F.col('flights_end_time').alias('flight_end_time'),
    F.col('parking_total_time').alias('client_parking_total_time')
)

# good
flights = flights.alias('flights')
parking = parking.alias('parking')

flights = flights.join(parking, on='flight_code', how='left')

flights = flights.select(
    F.col('flights.start_time').alias('flight_start_time'),
    F.col('flights.end_time').alias('flight_end_time'),
    F.col('parking.total_time').alias('client_parking_total_time')
)
```

In such cases, keep in mind:

1. It's probably best to drop overlapping columns *prior* to joining if you don't need both;
2. In case you do need both, it might be best to rename one of them prior to joining;
3. You should always resolve ambiguous columns before outputting a dataset. After the transform is finished running you can no longer distinguish them.

As a last word about joins, don't use `.dropDuplicates()` or `.distinct()` as a crutch.  If unexpected duplicate rows are observed, there's almost always an underlying reason for why those duplicate rows appear. Adding `.dropDuplicates()` only masks this problem and adds overhead to the runtime.

# Window Functions

Always specify an explicit frame when using window functions, using either [row frames](https://spark.apache.org/docs/latest/api/java/org/apache/spark/sql/expressions/WindowSpec.html#rowsBetween-long-long-) or [range frames](https://spark.apache.org/docs/latest/api/java/org/apache/spark/sql/expressions/WindowSpec.html#rangeBetween-long-long-). If you do not specify a frame, Spark will generate one, in a way that might not be easy to predict. In particular, the generated frame will change depending on whether the window is ordered (see [here](https://github.com/apache/spark/blob/v3.0.1/sql/catalyst/src/main/scala/org/apache/spark/sql/catalyst/analysis/Analyzer.scala#L2899)). To see how this can be confusing, consider the following example:

```python
from pyspark.sql import functions as F, Window as W
df = spark.createDataFrame([('a', 1), ('a', 2), ('a', 3), ('a', 4)], ['key', 'num'])

# bad
w1 = W.partitionBy('key')
w2 = W.partitionBy('key').orderBy('num')
 
df.select('key', F.sum('num').over(w1).alias('sum')).collect()
# => [Row(key='a', sum=10), Row(key='a', sum=10), Row(key='a', sum=10), Row(key='a', sum=10)]

df.select('key', F.sum('num').over(w2).alias('sum')).collect()
# => [Row(key='a', sum=1), Row(key='a', sum=3), Row(key='a', sum=6), Row(key='a', sum=10)]

df.select('key', F.first('num').over(w2).alias('first')).collect()
# => [Row(key='a', first=1), Row(key='a', first=1), Row(key='a', first=1), Row(key='a', first=1)]

df.select('key', F.last('num').over(w2).alias('last')).collect()
# => [Row(key='a', last=1), Row(key='a', last=2), Row(key='a', last=3), Row(key='a', last=4)]
```

It is much safer to always specify an explicit frame:
```python
# good
w3 = W.partitionBy('key').orderBy('num').rowsBetween(W.unboundedPreceding, 0)
w4 = W.partitionBy('key').orderBy('num').rowsBetween(W.unboundedPreceding, W.unboundedFollowing)
 
df.select('key', F.sum('num').over(w3).alias('sum')).collect()
# => [Row(key='a', sum=1), Row(key='a', sum=3), Row(key='a', sum=6), Row(key='a', sum=10)]

df.select('key', F.sum('num').over(w4).alias('sum')).collect()
# => [Row(key='a', sum=10), Row(key='a', sum=10), Row(key='a', sum=10), Row(key='a', sum=10)]

df.select('key', F.first('num').over(w4).alias('first')).collect()
# => [Row(key='a', first=1), Row(key='a', first=1), Row(key='a', first=1), Row(key='a', first=1)]

df.select('key', F.last('num').over(w4).alias('last')).collect()
# => [Row(key='a', last=4), Row(key='a', last=4), Row(key='a', last=4), Row(key='a', last=4)]
```

## Dealing with nulls

While nulls are ignored for aggregate functions (like `F.sum()` and `F.max()`), they will generally impact the result of analytic functions (like `F.first()` and `F.lead()`):
```python
df_nulls = spark.createDataFrame([('a', None), ('a', 1), ('a', 2), ('a', None)], ['key', 'num'])

df_nulls.select('key', F.first('num').over(w4).alias('first')).collect()
# => [Row(key='a', first=None), Row(key='a', first=None), Row(key='a', first=None), Row(key='a', first=None)]

df_nulls.select('key', F.last('num').over(w4).alias('last')).collect()
# => [Row(key='a', last=None), Row(key='a', last=None), Row(key='a', last=None), Row(key='a', last=None)]
```

Best to avoid this problem by enabling the `ignorenulls` flag:
```python
df_nulls.select('key', F.first('num', ignorenulls=True).over(w4).alias('first')).collect()
# => [Row(key='a', first=1), Row(key='a', first=1), Row(key='a', first=1), Row(key='a', first=1)]

df_nulls.select('key', F.last('num', ignorenulls=True).over(w4).alias('last')).collect()
# => [Row(key='a', last=2), Row(key='a', last=2), Row(key='a', last=2), Row(key='a', last=2)]
```

Also be mindful of explicit ordering of nulls to make sure the expected results are obtained:
```python
w5 = W.partitionBy('key').orderBy(F.asc_nulls_first('num')).rowsBetween(W.currentRow, W.unboundedFollowing)
w6 = W.partitionBy('key').orderBy(F.asc_nulls_last('num')).rowsBetween(W.currentRow, W.unboundedFollowing)

df_nulls.select('key', F.lead('num').over(w5).alias('lead')).collect()
# => [Row(key='a', lead=None), Row(key='a', lead=1), Row(key='a', lead=2), Row(key='a', lead=None)]

df_nulls.select('key', F.lead('num').over(w6).alias('lead')).collect()
# => [Row(key='a', lead=1), Row(key='a', lead=2), Row(key='a', lead=None), Row(key='a', lead=None)]
```

## Empty `partitionBy()`

Spark window functions can be applied over all rows, using a global frame. This is accomplished by specifying zero columns in the partition by expression (i.e. `W.partitionBy()`).

Code like this should be avoided, however, as it forces Spark to combine all data into a single partition, which can be extremely harmful for performance.

Prefer to use aggregations whenever possible:

```python
# bad
w = W.partitionBy()
df = df.select(F.sum('num').over(w).alias('sum'))

# good
df = df.agg(F.sum('num').alias('sum'))
```

# Chaining of expressions

Chaining expressions is a contentious topic, however, since this is an opinionated guide, we are opting to recommend some limits on the usage of chaining. See the conclusion of this section for a discussion of the rationale behind this recommendation.

Avoid chaining of expressions into multi-line expressions with different types, particularly if they have different behaviours or contexts. For example- mixing column creation or joining with selecting and filtering.

```python
# bad
df = (
    df
    .select('a', 'b', 'c', 'key')
    .filter(F.col('a') == 'truthiness')
    .withColumn('boverc', F.col('b') / F.col('c'))
    .join(df2, 'key', how='inner')
    .join(df3, 'key', how='left')
    .drop('c')
)

# better (seperating into steps)
# first: we select and trim down the data that we need
# second: we create the columns that we need to have
# third: joining with other dataframes

df = (
    df
    .select('a', 'b', 'c', 'key')
    .filter(F.col('a') == 'truthiness')
)

df = df.withColumn('boverc', F.col('b') / F.col('c'))

df = (
    df
    .join(df2, 'key', how='inner')
    .join(df3, 'key', how='left')
    .drop('c')
)
```

Having each group of expressions isolated into its own logical code block improves legibility and makes it easier to find relevant logic.
For example, a reader of the code below will probably jump to where they see dataframes being assigned `df = df...`.

```python
# bad
df = (
    df
    .select('foo', 'bar', 'foobar', 'abc')
    .filter(F.col('abc') == 123)
    .join(another_table, 'some_field')
)

# better
df = (
    df
    .select('foo', 'bar', 'foobar', 'abc')
    .filter(F.col('abc') == 123)
)

df = df.join(another_table, 'some_field', how='inner')
```

There are legitimate reasons to chain expressions together. These commonly represent atomic logic steps, and are acceptable. Apply a rule with a maximum of number chained expressions in the same block to keep the code readable.
We recommend chains of no longer than 5 statements.

If you find you are making longer chains, or having trouble because of the size of your variables, consider extracting the logic into a separate function:

```python
# bad
customers_with_shipping_address = (
    customers_with_shipping_address
    .select('a', 'b', 'c', 'key')
    .filter(F.col('a') == 'truthiness')
    .withColumn('boverc', F.col('b') / F.col('c'))
    .join(df2, 'key', how='inner')
)

# also bad
customers_with_shipping_address = customers_with_shipping_address.select('a', 'b', 'c', 'key')
customers_with_shipping_address = customers_with_shipping_address.filter(F.col('a') == 'truthiness')

customers_with_shipping_address = customers_with_shipping_address.withColumn('boverc', F.col('b') / F.col('c'))

customers_with_shipping_address = customers_with_shipping_address.join(df2, 'key', how='inner')

# better
def join_customers_with_shipping_address(customers, df_to_join):

    customers = (
        customers
        .select('a', 'b', 'c', 'key')
        .filter(F.col('a') == 'truthiness')
    )

    customers = customers.withColumn('boverc', F.col('b') / F.col('c'))
    customers = customers.join(df_to_join, 'key', how='inner')
    return customers
```

Chains of more than 3 statement are prime candidates to factor into separate, well-named functions since they are already encapsulated, isolated blocks of logic.

The rationale for why we've set these limits on chaining:

1. Differentiation between PySpark code and SQL code. Chaining is something that goes against most, if not all, other Python styling. You don’t chain in Python, you assign.
2. Discourage the creation of large single code blocks. These would often make more sense extracted as a named function.
3. It doesn’t need to be all or nothing, but a maximum of five lines of chaining balances practicality with legibility.
4. If you are using an IDE, it makes it easier to use automatic extractions or do code movements (i.e: `cmd + shift + up` in pycharm)
5. Large chains are hard to read and maintain, particularly if chains are nested.


# Multi-line expressions

The reason you can chain expressions is because PySpark was developed from Spark, which comes from JVM languages. This meant some design patterns were transported, specifically chainability. However, Python doesn't support multiline expressions gracefully and the only alternatives are to either provide explicit line breaks, or wrap the expression in parentheses. You only need to provide explicit line breaks if the chain happens at the root node. For example:

```python
# needs `\`
df = df.filter(F.col('event') == 'executing')\
       .filter(F.col('has_tests') == True)\
       .drop('has_tests')

# chain not in root node so it doesn't need the `\`
df = df.withColumn('safety', F.when(F.col('has_tests') == True, 'is safe')
                              .when(F.col('has_executed') == True, 'no tests but runs')
                              .otherwise('not safe'))
```

To keep things consistent, please wrap the entire expression into a single parenthesis block, and avoid using `\`:

```python
# bad
df = df.filter(F.col('event') == 'executing')\
    .filter(F.col('has_tests') == True)\
    .drop('has_tests')

# good
df = (
  df
  .filter(F.col('event') == 'executing')
  .filter(F.col('has_tests') == True)
  .drop('has_tests')
)
```




# Other Considerations and Recommendations

1. Be wary of functions that grow too large. As a general rule, a file
    should not be over 250 lines, and a function should not be over 70 lines.
2. Try to keep your code in logical blocks. For example, if you have
    multiple lines referencing the same things, try to keep them
    together. Separating them reduces context and readability.
3. Test your code! If you *can* run the local tests, do so and make
    sure that your new code is covered by the tests. If you can't run
    the local tests, build the datasets on your branch and manually
    verify that the data looks as expected.
4. Avoid `.otherwise(value)` as a general fallback. If you are mapping
    a list of keys to a list of values and a number of unknown keys appear,
    using `otherwise` will mask all of these into one value.
5. Do not keep commented out code checked in the repository. This applies
    to single line of codes, functions, classes or modules. Rely on git
    and its capabilities of branching or looking at history instead.
6. When encountering a large single transformation composed of integrating multiple different source tables, split it into the natural sub-steps and extract the logic to functions. This allows for easier higher level readability and allows for code re-usability and consistency between transforms.
7. Try to be as explicit and descriptive as possible when naming functions
    or variables. Strive to capture what the function is actually doing
    as opposed to naming it based the objects used inside of it.
8. Think twice about introducing new import aliases, unless there is a good
    reason to do so. Some of the established ones are `types` and `functions` from PySpark `from pyspark.sql import types as T, functions as F`.
9. Avoid using literal strings or integers in filtering conditions, new
    values of columns etc. Instead, to capture their meaning, extract them into variables, constants,
    dicts or classes as suitable. This makes the
    code more readable and enforces consistency across the repository.

WIP - To enforce consistent code style, each main repository should have [Pylint](https://www.pylint.org/) enabled, with the same configuration. We provide some PySpark specific checkers you can include in your Pylint to match the rules listed in this document. These checkers for Pylint still need some more energy put into them, but feel free to contribute and improve them.


[pylint]: https://www.pylint.org/
