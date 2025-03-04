import datetime
import json
import os
from math import pi

from .misc import run_path, search_and_replace


class ParametersFramework:
    def __init__(self):
        self.main_path = os.getcwd()

    def save(self, path=None):
        """
        Save parameters in json format

        :param path: Path where parameters should be saved. If no path is given main_path/parameters.json is used.
        :return: The path where the parameters were saved.
        """
        if not path:
            path = os.path.join(self.main_path, "parameters.json")
        if os.path.isfile(path):
            filename, extension = os.path.splitext(path)
            time = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
            os.rename(path, filename + "_back_" + time + extension)
        with open(path, "w") as file:
            json.dump(self.__dict__, file, indent=4, sort_keys=True)
        return path

    @classmethod
    def load(cls, path):
        """
        Loads the parameters saved in a json file into a new Parameter object.

        :param path: path of the json parameter file
        :return: a Parameter object
        """
        with open(path, "r") as file:
            params = json.load(file)
        if params["main_path"] != os.path.dirname(path):
            print("seams like the directory was moved. Parameter file is updated ...")
            search_and_replace(path, params["main_path"], os.path.dirname(path))
            with open(path, "r") as file:
                params = json.load(file)

        param = cls()
        param._setattrs(params)
        return param

    def _setattrs(self, dictionary):
        for key, value in dictionary.items():
            setattr(self, key, value)

    def __getitem__(self, item):
        return getattr(self, item)


class Parameters(ParametersFramework):
    """
    :ivar main_path: Defines a main path where the parameters and other things might be stored.
    :ivar n_neurons: List containing number of neurons for each layer up to the bottleneck layer.
        For example [128, 128, 2] stands for an autoencoder with the following architecture
        {i, 128, 128, 2, 128, 128, i} where i is the number of dimensions of the input data.
    :ivar activation_functions: List of activation function names as implemented in TensorFlow.
        For example: "relu", "tanh", "sigmoid" or "" to use no activation function.
        The encoder part of the network takes the activation functions from the list starting with the second element.
        The decoder part of the network takes the activation functions in reversed order starting with
        the second element form the back. For example ["", "relu", "tanh", ""] would result in a autoencoder with
        {"relu", "tanh", "", "tanh", "relu", ""} as sequence of activation functions.
    :ivar periodicity: Defines the distance between periodic walls for the inputs.
        For example 2pi for angular values in radians.
        All periodic data processed by EncoderMap must be wrapped to one periodic window.
        E.g. data with 2pi periodicity may contain values from -pi to pi or from 0 to 2pi.
        Set the periodicity to float("inf") for non-periodic inputs.

    :ivar learning_rate: Learning rate used by the optimizer.
    :ivar n_steps: Number of training steps.
    :ivar batch_size: Number of training points used in each training step
    :ivar summary_step: A summary for TensorBoard is writen every summary_step steps.
    :ivar checkpoint_step: A checkpoint is writen every checkpoint_step steps.

    :ivar dist_sig_parameters: Parameters for the sigmoid functions applied to the high- and low-dimensional distances
        in the following order (sig_h, a_h, b_h, sig_l, a_l, b_l)
    :ivar distance_cost_scale: Adjusts how much the distance based metric is weighted in the cost function.
    :ivar auto_cost_scale: Adjusts how much the autoencoding cost is weighted in the cost function.
    :ivar auto_cost_variant: defines how the auto cost is calculated. Must be one of: "mean_square", "mean_abs",
        "mean_norm"
    :ivar center_cost_scale: Adjusts how much the centering cost is weighted in the cost function.
    :ivar l2_reg_constant: Adjusts how much the l2 regularisation is weighted in the cost function.

    :ivar gpu_memory_fraction: Specifies the fraction of gpu memory blocked.
        If it is 0 memory is allocated as needed.
    :ivar analysis_path: A path that can be used to store analysis
    :ivar id: Can be any name for the run. Might be useful for example for specific analysis for different data sets.


    """

    def __init__(self):
        super(Parameters, self).__init__()
        self.n_neurons = [128, 128, 2]
        self.activation_functions = ["", "tanh", "tanh", ""]
        self.periodicity = 2 * pi

        self.learning_rate = 0.001
        self.n_steps = 100000
        self.batch_size = 256
        self.summary_step = 100
        self.checkpoint_step = 5000

        self.dist_sig_parameters = (4.5, 12, 6, 1, 2, 6)
        self.distance_cost_scale = 500
        self.auto_cost_scale = 1
        self.auto_cost_variant = "mean_abs"
        self.center_cost_scale = 0.0001
        self.l2_reg_constant = 0.001

        self.gpu_memory_fraction = 0
        self.analysis_path = ""
        self.id = ""


class ADCParameters(Parameters):
    """
    This is the parameter object for the AngleDihedralCartesianEncoder. It holds all the parameters that the Parameters
    object includes, plus the following parameters:


    :ivar cartesian_pwd_start: index of the first atom to use for the pairwise distance calculation
    :ivar cartesian_pwd_stop: index of the last atom to use for the pairwise distance calculation
    :ivar cartesian_pwd_step: step for the calculation of paiwise distances. E.g. for a chain of atoms
        N-C_a-C-N-C_a-C... cartesian_pwd_start=1 and cartesian_pwd_step=3 will result in using all C-alpha atoms for the
        pairwise distance calculation.

    :ivar use_backbone_angles: Allows to define whether backbone bond angles should be learned (True) or if instead mean
        values should be used to generate conformations (False)
    :ivar angle_cost_scale: Adjusts how much the angle cost is weighted in the cost function.
    :ivar angle_cost_variant: Defines how the angle cost is calculated. Must be one of: "mean_square", "mean_abs",
        "mean_norm"
    :ivar angle_cost_reference: Can be used to normalize the angle cost with the cost of same reference model (dummy)

    :ivar dihedral_cost_scale: Adjusts how much the dihedral cost is weighted in the cost function.
    :ivar dihedral_cost_variant: Defines how the dihedral cost is calculated. Must be one of: "mean_square", "mean_abs",
        "mean_norm"
    :ivar dihedral_cost_reference: Can be used to normalize the dihedral cost with the cost of same reference model
        (dummy)

    :ivar cartesian_cost_scale: Adjusts how much the cartesian cost is weighted in the cost function.
    :ivar cartesian_cost_scale_soft_start: Allows to slowly turn on the cartesian cost. Must be a tuple with
        (begin, ende) or (None, None) If begin and end are given, cartesian_cost_scale will be increased linearly in the
        given range
    :ivar cartesian_cost_variant: Defines how the cartesian cost is calculated. Must be one of: "mean_square",
        "mean_abs", "mean_norm"
    :ivar cartesian_cost_reference: Can be used to normalize the cartesian cost with the cost of same reference model
        (dummy)

    :ivar cartesian_dist_sig_parameters: Parameters for the sigmoid functions applied to the high- and low-dimensional
        distances in the following order (sig_h, a_h, b_h, sig_l, a_l, b_l)
    :ivar cartesian_distance_cost_scale: Adjusts how much the cartesian distance cost is weighted in the cost function.



    """

    def __init__(self):
        super(ADCParameters, self).__init__()

        self.cartesian_pwd_start = None
        self.cartesian_pwd_stop = None
        self.cartesian_pwd_step = None

        self.use_backbone_angles = False
        self.angle_cost_scale = 0
        self.angle_cost_variant = "mean_abs"
        self.angle_cost_reference = 1

        self.dihedral_cost_scale = 1
        self.dihedral_cost_variant = "mean_abs"
        self.dihedral_cost_reference = 1

        self.cartesian_cost_scale = 1
        self.cartesian_cost_scale_soft_start = (None, None)  # begin, end
        self.cartesian_cost_variant = "mean_abs"
        self.cartesian_cost_reference = 1

        self.cartesian_dist_sig_parameters = self.dist_sig_parameters
        self.cartesian_distance_cost_scale = 1

        self.auto_cost_scale = None
        self.distance_cost_scale = None
