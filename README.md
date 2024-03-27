## ayon-gaffer

This is an addon that adds Ayon to Gaffer. You can create publish types via the publisher; set framerange and publish renders via Deadline. 

#### This you need to know
* It only works with Ayon - not OpenPype
* It does not yet work with `ayon-core`
* It requires changes to the OpenPype core repo (https://github.com/ynput/OpenPype/pull/6254)
* For render publishing it _only_ does Deadline farm submissions


## A rough overview over render publishing
You need a `RenderSettings` node. Plug your scene into that one. Then add a `RenderLayer` node. Plug your settings into that. Finally through the menu `Ayon>Create` you can create a publish node (you can have multiple ones for different shots). Connect your `RenderLayer` nodes into that. Then publish!

Currently this setup has been used in production, but it's still very much under development.
