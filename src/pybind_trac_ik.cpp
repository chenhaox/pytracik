//
// Created by WRS on 8/12/2022.
//

#include "trac_ik.hpp" 
#include <pybind11/pybind11.h>
#include <pybind11/stl.h> // vector
#include <pybind11/operators.h>//operator
#include <pybind11/numpy.h>

namespace py = pybind11;

py::array_t<double> CartToJnt(TRAC_IK::TRAC_IK& t,
	py::array_t<double> init_q,
	double x,
	double y,
	double z,
	double qx,
	double qy,
	double qz,
	double qw) {

	// input
	py::buffer_info init_q_buf = init_q.request();
	double* init_q_buf_ptr = (double*)init_q_buf.ptr;
	// output
	py::array_t<double> result_array = py::array_t<double>(init_q_buf.size + 1);
	py::buffer_info result_array_buf = result_array.request();
	double* result_array_buf_ptr = (double*)result_array_buf.ptr;


	KDL::JntArray q(init_q_buf.size);
	KDL::JntArray result(init_q_buf.size);

	for (int i = 0; i < init_q_buf.size; i++)
		q(i) = init_q_buf_ptr[i];

	int r = t.CartToJnt(
		q,
		KDL::Frame(KDL::Rotation::Quaternion(qx, qy, qz, qw), KDL::Vector(x, y, z)),
		result);

	result_array_buf_ptr[0] = (float)r;
	if (r>=0) {
		for (int i = 0; i < init_q_buf.size; i++)
			result_array_buf_ptr[i + 1] = result(i);
	}
	return result_array;
}

py::array_t<double> JntToCart(TRAC_IK::TRAC_IK& t, py::array_t<double> cfg) {
    // change input joint configuration to KDL::JntArray
    py::buffer_info cfg_buf_info = cfg.request();
	double* cfg_buf_ptr = (double*)cfg_buf_info.ptr;
    KDL::JntArray q(cfg_buf_info.size);
    for (int i = 0; i < cfg_buf_info.size; i++)
        q(i) = cfg_buf_ptr[i];
    // solve forward kinematics
    KDL::Frame frame;
    KDL::Chain chain;
    t.getKDLChain(chain);
    KDL::ChainFkSolverPos_recursive fksolver(chain);
    int rc = fksolver.JntToCart(q, frame);
    // output
	py::array_t<double> result_array = py::array_t<double>({4,4});
	py::buffer_info result_array_buf = result_array.request();
	double* result_array_buf_ptr = (double*)result_array_buf.ptr;
    // If no solution, return empty vector which acts as None
    if (rc < 0)
        return result_array;
    // If solution, return 4x4 matrix
    for (int i = 0; i < 4; i++)
        for (int j = 0; j < 4; j++){
            result_array_buf_ptr[i * 4 + j] = frame(i, j);
    }
    return result_array;
}

int getNrOfJointsInChain(TRAC_IK::TRAC_IK& t, std::string base, std::string tip) {
	KDL::Chain chain;
	t.getKDLChain(chain);
	return (int)chain.getNrOfJoints();
}


PYBIND11_MODULE(pytracik_bindings, m) {
	py::class_<TRAC_IK::TRAC_IK>(m, "TRAC_IK")
		.def(py::init<std::string, std::string, std::string, double, double, TRAC_IK::SolveType>())
		.def("cart_to_jnt", &TRAC_IK::TRAC_IK::CartToJnt);

	py::enum_<TRAC_IK::SolveType>(m, "SolveType")
		.value("Speed", TRAC_IK::SolveType::Speed)
		.value("Distance", TRAC_IK::SolveType::Distance)
		.value("Manip1", TRAC_IK::SolveType::Manip1)
		.value("Manip2", TRAC_IK::SolveType::Manip2)
		.export_values();
	/*py::class_<KDL::JntArray>(m, "D_Jnt_Array")
		.def(py::init<unsigned int>())
		.def("cart_to_jnt", &TRAC_IK::TRAC_IK::CartToJnt);
	m.def("to_frame", &toKdlFrame)*/
    m.def("ik", &CartToJnt)
    .def("get_num_joints", &getNrOfJointsInChain).
    def("get_num_joints", &getNrOfJointsInChain).
    def("fk", &JntToCart);
}
