import json
import warnings
import numpy as np
import pymatgen.core as mg
from ase.io import read,write
# from ase.io.cif import read_cif, write_cif
from pymatgen.io.ase import AseAtomsAdaptor
from pymatgen.io.cif import CifParser
from pymatgen.core import Structure

def ase_format(mof):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            # mof_temp = Structure.from_file(mof,primitive=True)
            mof_temp = Structure.from_file(mof)
            mof_temp.to(filename=mof, fmt="cif")
            struc = read(mof)
            write(mof, struc)
            # print('Reading by ase: ' + mof)
    except:
        try:
            struc = read(mof)
            write(mof, struc)
            print('Reading by ase: ' + mof)
        except:
            print("An error occurred while reading: " + mof)

periodic_table_symbols = [
    'H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne', 'Na', 'Mg',
    'Al', 'Si', 'P', 'S', 'Cl', 'Ar', 'K', 'Ca', 'Sc', 'Ti', 'V', 'Cr',
    'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr',
    'Rb', 'Sr', 'Y', 'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd',
    'In', 'Sn', 'Sb', 'Te', 'I', 'Xe', 'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd',
    'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu', 'Hf',
    'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi', 'Po',
    'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th', 'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm',
    'Bk', 'Cf', 'Es', 'Fm', 'Md', 'No', 'Lr', 'Rf', 'Db', 'Sg', 'Bh', 'Hs',
    'Mt', 'Ds', 'Rg', 'Cn', 'Nh', 'Fl', 'Mc', 'Lv', 'Ts', 'Og'
    ]

def CIF2json(mof, save_path):
    try:
        structure = read(mof)
        struct = AseAtomsAdaptor.get_structure(structure)
    except:
        struct = CifParser(mof, occupancy_tolerance=10)
        struct.get_structures()
    _c_index, _n_index, _, n_distance = struct.get_neighbor_list(r=6, numerical_tol=0, exclude_self=True)
    _nonmax_idx = []
    for i in range(len(structure)):
        idx_i = (_c_index == i).nonzero()[0]
        idx_sorted = np.argsort(n_distance[idx_i])[: 200]
        _nonmax_idx.append(idx_i[idx_sorted])
    _nonmax_idx = np.concatenate(_nonmax_idx)
    index1 = _c_index[_nonmax_idx]
    index2 = _n_index[_nonmax_idx]
    dij = n_distance[_nonmax_idx]
    numbers = []
    # s_data = mg.Structure.from_file(mof)
    elements = [str(site.specie) for site in struct.sites]
    for i in range(len(elements)):
        ele = elements[i]
        atom_index = periodic_table_symbols.index(ele)
        numbers.append(int(int(atom_index)+1))
    nn_num = []
    for i in range(len(structure)):
        j = 0
        for idx in range(len(index1)):
            if index1[idx] == i:
                    j += 1
            else:
                    pass
        nn_num.append(j)
    data = {"rcut": 6.0,
            "numbers": numbers,
            "index1": index1.tolist(),
            "index2":index2.tolist(),
            "dij": dij.tolist(),
            "nn_num": nn_num}
    name = mof.split('.cif')[0]
    with open(save_path + name + ".json", 'w') as file:
        json.dump(data, file)

def pre4pre(mof, save_cell_dir, save_pos_dir):
    name = mof.split('.cif')[0]
    try:
        try:
            structure = mg.Structure.from_file(mof)
        except:
            try:
                atoms = read(mof)
                structure = AseAtomsAdaptor.get_structure(atoms)
            except:
                structure = CifParser(mof, occupancy_tolerance=10)
                structure.get_structures()
        coords = structure.frac_coords
        elements = [str(site.specie) for site in structure.sites]
        pos = []
        lattice = structure.lattice.matrix
        np.save(save_cell_dir + name + '_cell.npy', lattice)
        for i in range(len(elements)):
            x = coords[i][0]
            y = coords[i][1]
            z = coords[i][2]
            pos.append([float(x),float(y),float(z)])
        np.save(save_pos_dir + name + '_pos.npy', pos)
    except Exception as e:
        pass
        # print(f"An error occurred while finding cell and position of {name}: {e}")

def n_atom(mof):
    structure = mg.Structure.from_file(mof)
    name = mof.split('.cif')[0]
    elements = [str(site.specie) for site in structure.sites]
    print("number of atoms of " + name +": ", len(elements))
    return len(elements)

def write4cif(mof,chg,save_dir,digits,charge = True):
    name = mof.split('.cif')[0]
    if charge:
        gcn_charge = np.load(chg + name + "_charge.npy")
        sum_chg = sum(gcn_charge)
        charges = []
        digits=int(digits)
        for c in gcn_charge:
            cc = c - sum_chg/len(gcn_charge)
            # charges.append(round(c, digits))
            charges.append(round(cc, digits))

        with open(name + ".cif", 'r') as file:
            lines = file.readlines()
        lines[0] = "# generated by Guobin Zhao (Prof.Chung, Yongchul G, https://sites.google.com/view/mtap-lab/home, Pusan National University)\n"
        lines[1] = "data_structure\n"
        for i, line in enumerate(lines):
            if '_atom_site_occupancy' in line:
                lines.insert(i + 1, "  _atom_site_charge\n")
                break
        charge_index = 0
        for j in range(i + 2, len(lines)):
            if charge_index < len(charges):
                lines[j] = lines[j].strip() + " " + str(charges[charge_index]) + "\n"
                charge_index += 1
            else:
                break
        with open(save_dir + name + "_gcn.cif", 'w') as file:
            file.writelines(lines)
        file.close()

    with open(save_dir + name + "_gcn.cif", 'r') as file:
        content = file.read()
    file.close()

    new_content = content.replace('_space_group_name_H-M_alt', '_symmetry_space_group_name_H-M')
    new_content = new_content.replace('_space_group_IT_number', '_symmetry_Int_Tables_number')
    new_content = new_content.replace('_space_group_symop_operation_xyz', '_symmetry_equiv_pos_as_xyz')

    with open(save_dir + name + "_gcn.cif", 'w') as file:
        file.write(new_content)
    file.close()
    
    
