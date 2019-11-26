module block(x1,x2,x3,r1,r2,r3,c0,c1) {
    translate([x1+0.5,x2+0.5,x3+0.5]) {
        rotate([r1,r2,r3]) {
            translate([-0.5,-0.5,-0.5]) {
                color(c0) {
                    difference() {
                        linear_extrude(height = 1) {
                            polygon([[0,0],[1,0],[1,1]]);
                        }
                        translate([-0.026,0.026,0.08]) {
                            linear_extrude(height = 0.84) {
                                polygon([[0.1,0.05],[0.95,0.05],[0.95,0.9]]);
                            }
                        }
                    }
                }
                color(c1) {
                    translate([-0.025,0.025,0.08]) {
                        linear_extrude(height = 0.84) {
                            polygon([[0.1,0.05],[0.95,0.05],[0.95,0.9]]);
                        }
                    }
                }
            }
        }
    }
}

