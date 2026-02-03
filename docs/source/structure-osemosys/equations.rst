###########################
Equations
###########################

The OSeMOSYS code is organized into blocks of equations, consisting of a single objective function and multiple constraints. This modular structure enables users to add or remove specific functionalities as needed. Its flexibility makes OSeMOSYS suitable for a wide variety of applications, accommodating different scales, levels of complexity, and analytical goals.

Objective function
----------------------------
This equation represents the overall objective of the model. The default in OSeMOSYS is to minimise the total system cost, over the entire model period.

.. literalinclude:: documents/code/model_organized.txt
   :language: ampl
   :lines: 156-159

Capacity Adequacy A
----------------------------
Used to first calculate total capacity of each technology for each year based on existing capacity from before the model period (*ResidualCapacity*), *AccumulatedNewCapacity* during the modelling period, and *NewCapacity* installed in each year. It is then ensured that this Capacity is sufficient to meet the *RateOfTotalActivity* in each TimeSlice and Year. An additional constraint based on the size, or capacity, of each unit of a Technology is included (*CapacityOfOneTechnologyUnit*). This stipulates that the capacity of certain Technology can only be a multiple of the user-defined *CapacityOfOneTechnologyUnit*.

.. literalinclude:: documents/code/model_organized.txt
   :language: ampl
   :lines: 167-171

NOTE: OSeMOSYS uses Mixed Integer Programming to solve models that define *CapacityOfTechnologyUnit*. Using this parameter is likely to increase the model computation time.

Capacity Adequacy B
----------------------------
Ensures that adequate capacity of technologies is present to at least meet the average annual demand.

.. literalinclude:: documents/code/model_organized.txt
   :language: ampl
   :lines: 175

Energy Balance A
----------------------------
Ensures that demand for each commodity is met in each TimeSlice.

.. literalinclude:: documents/code/model_organized.txt
   :language: ampl
   :lines: 179-182

Energy Balance B
----------------------------
Ensures that demand for each commodity is met in each Year.

.. literalinclude:: documents/code/model_organized.txt
   :language: ampl
   :lines: 186

Accounting Technology Production/Use
---------------------------------------------
Accounting equation used to generate a specific intermediate variables: *TotalAnnualTechnologyActivityByMode*.

.. literalinclude:: documents/code/model_organized.txt
   :language: ampl
   :lines: 190

Storage Equations
----------------------------
This block of equations governs the charging, discharging, and accounting of energy storage systems across multiple time dimensions (season, day type, and time slice) within the model. It ensures energy balance consistency and temporal linkage in storage behavior.

.. literalinclude:: documents/code/model_organized.txt
   :language: ampl
   :lines: 194-209

Storage Constraints
---------------------------------
This block of equations defines the operational and capacity boundaries for energy storage systems throughout their time resolution ensuring that storage levels remain within physically and technically feasible limits over seasons, day types, and time brackets.

.. literalinclude:: documents/code/model_organized.txt
   :language: ampl
   :lines: 225-234

Storage Investments
----------------------------
Calculates the total discounted capital costs expenditure for each storage technology in each year.

.. literalinclude:: documents/code/model_organized.txt
   :language: ampl
   :lines: 238-243

Capital Costs
--------------------
Calculates the total undiscounted capital cost expenditure for each technology in each year.

.. literalinclude:: documents/code/model_organized.txt
   :language: ampl
   :lines: 257

Salvage Value
--------------------
Calculates the fraction of the initial capital cost that can be recouped at the end of a technologies operational life.

.. literalinclude:: documents/code/model_organized.txt
   :language: ampl
   :lines: 261-264

Operating Costs
--------------------
Calculates the total variable and fixed operating costs for each technology, in each year.

.. literalinclude:: documents/code/model_organized.txt
   :language: ampl
   :lines: 268-269

Total Capacity Constraints
----------------------------------------
Ensures that the total capacity of each technology in each year is greater than and less than the user-defined parameters *TotalAnnualMinCapacityInvestment* and *TotalAnnualMaxCapacityInvestment* respectively.

.. literalinclude:: documents/code/model_organized.txt
   :language: ampl
   :lines: 273-274

New Capacity Constraints
-----------------------------------
Ensures that the new capacity of each technology installed in each year is greater than and less than the user-defined parameters *TotalAnnualMinCapacityInvestment* and *TotalAnnualMaxCapacityInvestment* respectively.

.. literalinclude:: documents/code/model_organized.txt
   :language: ampl
   :lines: 278-279

Annual Activity Constraints
-----------------------------------------
Ensures that the total activity of each technology over each year is greater than and less than the user-defined parameters *TotalTechnologyAnnualActivityLowerLimit* and *TotalTechnologyAnnualActivityUpperLimit* respectively.

.. literalinclude:: documents/code/model_organized.txt
   :language: ampl
   :lines: 283-285

Total Activity Constraints
-------------------------------------------------
Ensures that the total activity of each technology over the entire model period is greater than and less than the user-defined parameters *TotalTechnologyModelPeriodActivityLowerLimit* and *TotalTechnologyModelPeriodActivityUpperLimit* respectively.

.. literalinclude:: documents/code/model_organized.txt
   :language: ampl
   :lines: 289-291

Emissions Accounting
-------------------------------------------
Calculates the annual and model period emissions from each technology, for each type of emission. It also calculates the total associated emission penalties, if any. Finally, it ensures that emissions are maintained before stipulated limits that may be defined for each year and/or the entire model period.

.. literalinclude:: documents/code/model_organized.txt
   :language: ampl
   :lines: 296-305

Input To Capacity Ratios
-------------------------------------------
This block defines the technical input requirements associated with the installed or newly added capacity of each technology. These equations ensure that the use of input commodities is proportional to the capacity available or added in the model year, enforcing design-specific efficiency or conversion rates.

.. literalinclude:: documents/code/model_organized.txt
   :language: ampl
   :lines: 309-310

Mode-specific Constraints	
-------------------------------------------
This block of constraints governs the total annual activity levels of technologies operating in different modes of operation (e.g., cogeneration modes). These constraints allow the model to control how technologies behave not just in total, but also within each of their defined modes.

.. literalinclude:: documents/code/model_organized.txt
   :language: ampl
   :lines: 314-317

User-defined Constraints	
-------------------------------------------
This block introduces a flexible framework for modeling custom constraints that reflect user-defined relationships between technology capacities, new investments, and activity levels. These constraints allow model users to encode additional system rules, targets, or boundaries without modifying the model’s core structure.

.. literalinclude:: documents/code/model_organized.txt
   :language: ampl
   :lines: 321-328