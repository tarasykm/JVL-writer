import aerosandbox as asb
import aerosandbox.numpy as np

class JetParam:
    def __init__(self, hdisk=0.45, fh=1.0, djet0=-2.0, djet1=-0.2, djet3=-0.0003):
        """
        Jet Param class
        
        :param hdisk: Disk height scaling factor
        :param fh: Type of propulsor (0 for long-duct, 1 for no-duct)
        :param djet0: Jet deviation angle due to TE wedge angle
        :param djet1: Incomplete jet turning due to finite jet height/flap ratio
        :param djet3: BL separation effect on jet turning
        """
        self.hdisk = hdisk
        self.fh = fh
        self.djet0 = djet0
        self.djet1 = djet1
        self.djet3 = djet3

class JetControl:
    def __init__(self, jet_name, gain, sgn_dup):
        """
        Jet Control class
        
        :param jet_name: Name of the jet control variable
        :param gain: Control gain (Delta_Vjet/Vinf per jet variable)
        :param sgn_dup: Symmetric (1) or differential (-1) blowing
        :param hdisk: Disk height scaling factor
        :param fh: Type of propulsor (0 for long-duct, 1 for no-duct)
        :param djet0: Jet deviation angle due to TE wedge angle
        :param djet1: Incomplete jet turning due to finite jet height/flap ratio
        :param djet3: BL separation effect on jet turning
        """
        self.jet_name = jet_name
        self.gain = gain
        self.sgn_dup = sgn_dup

class WingJSec(asb.WingXSec):
    def __init__(self, xyz_le, chord, twist, airfoil, control_surfaces=None,
                 jet_params=[], jet_controls=[]):
        """
        Extended WingXSec class with Jet Control (JETCONTROL & JETPARAM)
        
        :param xyz_le: Leading edge position [x, y, z]
        :param chord: Chord length at this section
        :param twist: Twist angle at this section
        :param airfoil: AeroSandbox Airfoil object
        :param control_surfaces: List of control surfaces
        :param jet_name: Name of the jet control variable
        :param gain: Control gain (Delta_Vjet/Vinf per jet variable)
        :param sgn_dup: Symmetric (1) or differential (-1) blowing
        :param hdisk: Disk height scaling factor
        :param fh: Type of propulsor (0 for long-duct, 1 for no-duct)
        :param djet0: Jet deviation angle due to TE wedge angle
        :param djet1: Incomplete jet turning due to finite jet height/flap ratio
        :param djet3: BL separation effect on jet turning
        """
        super().__init__(xyz_le=xyz_le, chord=chord, twist=twist, airfoil=airfoil, control_surfaces=control_surfaces)
        self.jet_params = jet_params
        self.jet_controls = jet_controls
    
    def avl_jet_control(self):
        """Returns formatted AVL jet control data"""
        return f"JETCONTROL\n {self.jet_name}  {self.gain:.3f}  {self.sgn_dup:.3f}\n" \
               f"JETPARAM\n {self.hdisk:.3f}  {self.fh:.3f}  {self.djet0:.3f}  {self.djet1:.3f}  {self.djet3:.6f}\n"
