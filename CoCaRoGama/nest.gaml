/**
* Name: nest
* Based on the internal empty template. 
* Author: ashfa
* Tags: 
*/


model nest

import "cell_.gaml"

/* Insert your model definition here */

species nest {
	rgb color;
	//cell myCell update: cell first_with (each overlaps self);
	//cell myCell <- cell(location);  // fastest
	cell myCell <- cell closest_to self;	
	
	
	aspect default {        
		draw circle(1) color: #white border: color;
		draw string("Nest") color: color size:1;			
    }
    
    
    aspect icon {        
    	image_file nest_shape <- file('../images/bin.png');
		float cell_width <- world.shape.width / 50;
      	float cell_height <- world.shape.height / 50;
		draw nest_shape size: {cell_width, cell_height}; 
    }
}










