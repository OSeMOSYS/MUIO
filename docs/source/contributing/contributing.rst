###########################
Contributing
###########################

We warmly welcome anyone interested in MUIO and the broader OSeMOSYS ecosystem! Whether you have ideas, suggestions, bug reports, or would like to contribute improvements, your input is highly valued.

How You Can Contribute
---------------------------

🧠 `Code Contributions`_

Help us enhance MUIO by adding new functionalities, fixing bugs, or optimizing model performance.

📚 `Documentation`_

Support the community by expanding or refining the documentation—add new sections, correct errors, or improve clarity for new users.

📂 `Examples and Use Cases`_

Share your modelling examples or country applications. These can be valuable learning tools for others in the community.


Code Contributions
-------------------

Want to suggest a fix or add a feature? Here's a quick and easy workflow:

1.	Fork the repository: Click the “Fork” button on the  `MUIO GitHub page <https://github.com/OSeMOSYS/MUIO>`_

2.	Clone your fork: Copy the link to your fork and run:

.. code:: bash

    git clone https://github.com/<your-username>/MUIO.git
   
3.	Make your changes: Create a new branch and make your edits or improvements in the code. 

4.	Test your changes: If there are tests, run them locally. If not, just make sure your edits work as expected.

5.	Push and open a pull request: Push your branch to your fork and go to GitHub to open a pull request.

Documentation
-------------------

We aim to keep the MUIO documentation clear, helpful, and up to date. If you notice any gaps, outdated content, or unclear explanations, your help in improving it is greatly appreciated.

How to Contribute to the Docs: 

1. Find something to improve  
   Spotted a typo, unclear sentence, or missing sections.

2. Edit directly on GitHub  

   - On any documentation page, click the book icon (📖) at the bottom-left corner.  
   - Then click “Edit on GitHub” – this will take you to the exact source file.

3. Make your changes  
   Use GitHub’s built-in editor to edit the file directly.

4. Propose your edit  
   Once done, commit the changes and open a pull request. We’ll review and merge it!


Examples and Use Cases
-------------------

Have you built a useful energy model using MUIO? We'd love to include it as an example to help others learn and build faster. Here's how to contribute an example to the documentation:

✅ What Makes a Good Example?
^^^^^^^^^^^^^^^^^^^^^^

We welcome examples that:

* Use MUIO in real or hypothetical case studies (e.g. countries, regions, sectors).

* Demonstrate specific features (e.g. multi-regional modelling, transport sector, emissions).

* Include complete data files, clear naming, and a brief description.

* Are small enough to run quickly (or include a simplified version).

🚀 How to Contribute an Example
^^^^^^^^^^^^^^^^^^^^^^

1. Prepare your files

   - Organize your example in a folder under ``examples/`` (e.g. ``examples/CountryName/``).
   - Include:
     
     - Model input file (.zip)
     - A ``README.md`` describing the model purpose, data source, and assumptions
     - *(Optional)* Output plots or summary results

2. Fork and clone the MUIO repository.

3. Add your folder under ``/examples``.  
   If it’s large, consider linking to an external repository or storage (e.g. Zenodo, Figshare).

4. Add a reference in the documentation

   - Edit the examples section in the documentation (``docs/source/examples.rst``).
   - Add a short entry linking to your example folder or external repo.

5. Create a pull request  
   Submit your changes with a short description of your example.

📝 Licensing and Attribution
^^^^^^^^^^^^^^^^^^^^^^

* Please include a note in your README.md indicating data sources and your preferred citation (if any).

* Make sure you have the right to share the data and code you include.
