import { DataModel } from "../../Classes/DataModel.Class.js";

export class Model {

    constructor(casename, genData, RYTCndata, group, PARAMETERS, param) {
        this.d = 2;
        this.decimal = 'd' + this.d;
        if (casename) {

            let datafields = [];
            let columns = [];

            let years = genData['osy-years'];
            let constraints = genData['osy-constraints'];
            let scenarios = genData['osy-scenarios'];

            let RYTCngrid = DataModel.RYTCngrid(genData, RYTCndata);
            let techIds = DataModel.TechId(genData);
            let conId = DataModel.ConId(genData);
            let constraintsMC = DataModel.constraintsCM(constraints);
            let ConstraintTechs = DataModel.constraintTechs(genData)
            let PARAMNAMES = DataModel.ParamName(PARAMETERS[group]);

            let scClass = {};

            $.each(scenarios, function (id, obj) {
                scClass[obj.ScenarioId] = 'SC_' + id;
            });

                        var cellclass = function (row, columnfield, value, data) {
                return scClass[data.ScId];
            }
            
            datafields.push({ name: 'ScId', type: 'string' });
            datafields.push({ name: 'Sc', type: 'string' });

            datafields.push({ name: 'TechId', type: 'string' });
            datafields.push({ name: 'Tech', type: 'string' });
            datafields.push({ name: 'ConId', type: 'string' });
            datafields.push({ name: 'Con', type: 'string' });
            datafields.push({ name: 'ScDesc', type: 'string' });
            datafields.push({ name: 'TechDesc', type: 'string' });
            datafields.push({ name: 'ConDesc', type: 'string' });

            columns.push({ text: 'Scenario', datafield: 'Sc', pinned: true, editable: false, align: 'left', cellclassname: cellclass, filterable: false, menu:false });
            columns.push({ text: 'Technology', datafield: 'Tech', pinned: true, editable: false, align: 'center', cellclassname: cellclass, filterable: true })
            columns.push({ text: 'Constraint', datafield: 'Con', pinned: true, editable: false, align: 'center', cellclassname: cellclass, filterable: false, menu:false })


            let validation = function (cell, value) {
                if (value < 0) {
                    return { result: false, message: 'Value must be positive!' };
                } else {
                    return true;
                }
            }



            let cellsrenderer = function (row, columnfield, value, defaulthtml, columnproperties) {
                if (value === null || value === '') {
                    return '<span style="margin: 4px; float:right; ">n/a</span>';
                } else {
                    var formattedValue = $.jqx.dataFormat.formatnumber(value, this.decimal);
                    return '<span style="margin: 4px; float:right; ">' + formattedValue + '</span>';
                }

            }.bind(this);


            let initeditor = function (row, cellvalue, editor, data) {
                var scId = $('#osy-gridRYTCn').jqxGrid('getcellvalue', row, 'ScId');
                if (scId !== 'SC_0') {
                    editor.jqxNumberInput({ decimalDigits: this.d, spinButtons: true, allowNull: true });
                    $('#' + editor[0].id + ' input').keydown(function (event) {
                        if (event.keyCode === 46 || event.keyCode === 8) {
                            $('#' + editor[0].id).val(null);
                        }
                    })
                }
                else{
                    editor.jqxNumberInput({ decimalDigits: this.d, spinButtons: true, allowNull: false });
                    editor.val(cellvalue);
                }
            }.bind(this);

            let geteditorvalue =  function (row, cellvalue, editor) {
                return editor.val() == null ? null : editor.val();
            }

            $.each(years, function (id, year) {
                datafields.push({ name: year, type: 'number' });
                columns.push({
                    text: year, datafield: year, cellsalign: 'right', align: 'center', columntype: 'numberinput', 
                    cellsformat: this.decimal, minWidth: 55, maxWidth: 110,
                    groupable: false,
                    filterable: false,
                    sortable: false,
                    initeditor: initeditor,
                    //validation: validation,
                    cellsrenderer: cellsrenderer,
                    cellclassname: cellclass,
                    geteditorvalue: geteditorvalue, menu:false
                });
            }.bind(this));


            var srcGrid = {
                datatype: "json",
                localdata: RYTCngrid,
                root: param,
                datafields: datafields,
            };

            this.casename = casename;
            this.years = years;
            this.techs = ConstraintTechs;
            this.techIds = techIds;
            this.conId = conId;
            this.cons = constraintsMC;
            this.scenarios = scenarios;
            this.scenariosCount = scenarios.length;
            this.datafields = datafields;
            this.columns = columns;
            this.gridData = RYTCngrid;
            this.genData = genData;
            this.param = param;
            this.PARAMNAMES = PARAMNAMES;
            this.group = group;
            this.srcGrid = srcGrid;
            this.PARAMETERS = PARAMETERS;
        } else {
            this.casename = null;
            this.years = null;
            this.techs = null;
            this.datafields = null;
            this.columns = null;
            this.gridData = null;
            this.genData = null;
            this.param = param;
            this.PARAMNAMES = PARAMNAMES;
            this.group = group;
            this.srcGrid = null;
            this.PARAMETERS = PARAMETERS;
        }
    }
}