import stretch_body.hello_utils as hello_utils
import importlib

def generate_user_params_from_template(variant_name, fleet_dir=None):
    param_module_name = 'stretch_body.robot_params_' + variant_name
    user_params = getattr(importlib.import_module(param_module_name), 'user_params_template')
    user_header = getattr(importlib.import_module(param_module_name), 'user_params_header')
    hello_utils.write_fleet_yaml('stretch_user_params.yaml',user_params,fleet_dir,user_header)

def generate_configuration_params_from_template(variant_name, batch_name, robot_serial_no, fleet_dir=None):
    param_module_name = 'stretch_body.robot_params_' + variant_name
    config_params = getattr(importlib.import_module(param_module_name), 'configuration_params_template')
    config_header = getattr(importlib.import_module(param_module_name), 'configuration_params_header')
    config_params['robot']['batch_name']=batch_name
    config_params['robot']['serial_no']=robot_serial_no
    hello_utils.write_fleet_yaml('stretch_configuration_params.yaml', config_params, fleet_dir,config_header)

def copy_over_params(dest_dict, src_dict,dest_dict_name='',src_dict_name=''):
    """
    Copy atomic values (list, numbers, strings) from src to dest
    Only if the key is found in the dest dict and types are the same
    """
    for k in dest_dict.keys():
        if k in src_dict:
            if type(src_dict[k])==type(dest_dict[k]):
                if type(src_dict[k])==dict:
                    copy_over_params(dest_dict[k],src_dict[k],dest_dict_name+'.'+str(k), src_dict_name+'.'+str(k))
                else:
                    dest_dict[k]=src_dict[k]
            else:
                print('Migration error. Type mismatch for key %s during copy from %s to %s. From type %s. To type %s'%(k,src_dict_name,dest_dict_name,str(type(src_dict[k])),str(type(dest_dict[k]))))
                print('Values Src | Dest: ',src_dict[k],dest_dict[k])
        else:
            print('Migration error. Parameter %s not found during copy from %s to %s'%(k,src_dict_name,dest_dict_name))

def param_change_check(new_dict,prior_dict,num_warnings,new_dict_name='',prior_dict_name=''):
    for k in new_dict.keys():
        if k in prior_dict:
            if type(new_dict[k])==dict:
                    num_warnings=param_change_check(new_dict[k],prior_dict[k],num_warnings,new_dict_name+'.'+k,prior_dict_name+'.'+k)
            else:
                if new_dict[k]!=prior_dict[k]:
                    print('Warning. Value change in %s from %s to %s'%(new_dict_name+'.'+k,prior_dict[k],new_dict[k]))
                    num_warnings=num_warnings+1
    return num_warnings


def param_added_check(new_dict,prior_dict,num_warnings,new_dict_name='',prior_dict_name=''):
    for k in new_dict.keys():
        if k in prior_dict:
            if type(new_dict[k])==dict:
                    num_warnings=param_added_check(new_dict[k],prior_dict[k],num_warnings,new_dict_name+'.'+k,prior_dict_name+'.'+k)
        else:
            print('Warning. Parameter introduced: %s'%(new_dict_name+'.'+k))
            num_warnings=num_warnings+1
    return num_warnings

def param_dropped_check(new_dict,prior_dict,num_warnings,new_dict_name='',prior_dict_name=''):
    for k in prior_dict.keys():
        if k in new_dict:
            if type(prior_dict[k])==dict:
                    num_warnings=param_dropped_check(new_dict[k],prior_dict[k],num_warnings,new_dict_name+'.'+k,prior_dict_name+'.'+k)
        else:
            print('Warning. Parameter %s dropped'%(prior_dict_name+'.'+k))
            num_warnings=num_warnings+1
    return num_warnings

#Todo: make generic for future migrations / parameter org changes. Do we version parameter orgs?
def migrate_params_RE1P0(fleet_path, fleet_id):
    """
    The parameter organization has changed between RE1P0 and RE1P1 in the following ways
    1. stretch_re1_user_params.yaml is now named stretch_user_params.yaml
    2. stretch_configuration_params.yaml is introduced
    3. stretch_factory_params.yaml is deprecated
    4. Parameter precendence has changed as described in stretch_body.robot_params.py

    Migration algorithm:
    ---------------------------------

    #Construct the original robot_params dictionary without user data (O)
    #Construct a new Configuration Params dictionary (C)
    #Copy data from O to C provided the parameter exists in C (otherwise drop the parameter)
    #Save C to stretch_configuration_params.yaml
    #Copy the original user params to stretch_user_params.yaml
    #Verify that the new robot parameters match the old (modulo designated exceptions)

    """
    #Point to the data to be migrated
    hello_utils.set_fleet_directory(fleet_path, fleet_id)
    #Get the original parameter dictionaries
    U = hello_utils.read_fleet_yaml('stretch_re1_user_params.yaml')
    F = hello_utils.read_fleet_yaml(U.get('factory_params', ''))

    #Construct the original robot_params dictionary without user data (O)
    import stretch_body.robot_params_RE1P0
    import copy
    O = copy.deepcopy(F)
    hello_utils.overwrite_dict(O, stretch_body.robot_params_RE1P0.factory_params_deprecated)
    for external_params_module in U.get('params', []):
        hello_utils.overwrite_dict(O, getattr(importlib.import_module(external_params_module), 'params'))

    #Construct a new Configuration Params dictionary (C)
    generate_configuration_params_from_template(variant_name='RE1P0', batch_name=O['robot']['batch_name'], robot_serial_no=O['robot']['serial_no'], fleet_dir=None)
    C = hello_utils.read_fleet_yaml('stretch_configuration_params.yaml')
    # Manually copy over special cases from )
    O['robot']['variant_name'] = C['robot']['variant_name']
    O['robot']['d435i_serial_no'] = C['robot']['d435i_serial_no']
    #Now copy over rest of O data to C
    copy_over_params(C,O,'NewParams','OldParams')
    hello_utils.write_fleet_yaml('stretch_configuration_params.yaml', C, None,stretch_body.robot_params_RE1P0.configuration_params_header)

    #Write user params to new yaml
    generate_user_params_from_template('RE1P0')
    hello_utils.write_fleet_yaml('stretch_user_params.yaml', U, None,stretch_body.robot_params_RE1P0.user_params_header)

    #Now read in the new parameter data

    import stretch_body.robot_params
    (UU,R)=stretch_body.robot_params.RobotParams().get_params()

    #Copy in user data to create the complete original parameter set to compare to
    hello_utils.overwrite_dict(O,U)

    #Now check for differences
    added_warnings=param_added_check(R,O,0,'NewParams','OldParams')
    dropped_warnings=param_dropped_check(R,O,0,'NewParams','OldParams')
    change_warnings=param_change_check(R,O,0,'NewParams','OldParams')

    print('Diff check: Added %d, Dropped %d, Changed %d'%(added_warnings,dropped_warnings,change_warnings))
