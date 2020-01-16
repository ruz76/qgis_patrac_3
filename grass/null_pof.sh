r.mapcalc expression='coords_friction_slope=friction_slope * coords'
r.mapcalc expression='friction_null=friction_slope';
r.null map=friction_null null=0
r.reclass input=friction_null output=friction_null_rec rules=-
<<
0 = 1
* = null
end
EOF
r.buffer input=friction_null_rec output=friction_null_rec_buf_10 distances=10
r.null friction_null_rec_buf_10 setnull=1
r.mapcalc expression='friction_flat=1'
r.cost input=friction_flat output=friction_flat_cost start_points=coords --o
r.mapcalc expression='friction_flat_cost_buf=friction_flat_cost*friction_null_rec_buf_10'
#TODO get min value r.info friction_flat_cost_buf
r.reclass input=friction_flat_cost_buf output=friction_flat_cost_buf_min rules=-
<<
minvalue = 1
* = null
end
EOF
r.to.vect input=friction_flat_cost_buf_min output=friction_flat_cost_buf_min type=point
#TODO keep just one point - meybe not - we can do it from more locations
