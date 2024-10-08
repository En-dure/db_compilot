DROP TABLE IF EXISTS `2023`;
CREATE TABLE `2023`  (
  `年月` text  COMMENT '格式为202301,表示2023年1月，共包含2023年的12个月,依次类推，例如202302代表2023年2月',
  `科室名称` text ,
  `科室名称01` text  ,
  `病区代码` text  ,
  `病区名称` text  ,
  `门急诊人次` text  ,
  `门诊人次` text  ,
  `门诊医保人次` text  ,
  `门诊自费人次` text  ,
  `核酸人次` text  ,
  `专家门诊人次` text  ,
  `专病门诊人次` text  ,
  `特需门诊人次` text  ,
  `互联网接诊人次` text  ,
  `急诊人次` text  ,
  `急诊医保人次` text  ,
  `儿科人数` text  ,
  `儿科门诊人数` text  ,
  `儿科急诊人数` text  ,
  `儿科发热人数` text  ,
  `发热人数` text  ,
  `出院人数` text  COMMENT '出院人次',
  `结账人数` text  ,
  `死亡人数` text  ,
  `重症人数` text  ,
  `眼科日间手术数` text  ,
  `门诊日间手术数` text  ,
  `住院日间手术数` text  ,
  `介入手术数` text  ,
  `心内手术数` text  ,
  `手术登记数` text  ,
  `院内手术例数` text  ,
  `院内三四级手术例数` text  ,
  `术前平均等待日` text  ,
  `国考四级手术人数` text  ,
  `国考微创手术人数` text  ,
  `国考手术人数` text  ,
  `住院抗生素DDDs` text  ,
  `住院天数` text  ,
  `抗菌药物使用强度` text  ,
  `门诊抗菌药处分数` text  ,
  `门诊处方数` text  ,
  `门诊抗菌药物使用比率` text  ,
  `急诊抗菌药处分数` text  ,
  `急诊处方数` text  ,
  `急诊抗菌药物使用比率` text  ,
  `住院抗菌药使用人次` text  ,
  `出院人次` text  ,
  `住院抗菌药物使用比率` text  ,
  `本期占床人次` text  ,
  `院内床数` text  ,
  `核定床位使用率` text  ,
  `本期出院人数` text  ,
  `转往他科` text  ,
  `病床周转率` text  ,
  `平均住院日` text  ,
  `门急诊总费用` text COMMENT '门急诊总收入',
  `门急诊药费` text  ,
  `门急诊中成药费` text  ,
  `门急诊草药费` longtext  ,
  `门急诊中草药费` text  ,
  `门急诊耗材费` text COMMENT '门急诊卫生材料',
  `门急诊检查费` text  ,
  `门急诊检验费` text  ,
  `门急诊医疗服务费` text  ,
  `门急诊医保费用` text  ,
  `住院总费用` text  ,
  `住院伙食费` text  ,
  `住院药费` text  ,
  `住院中成药费` text  ,
  `住院草药费` text  ,
  `住院中草药费` text  ,
  `住院耗材费` text COMMENT '住院卫生材料',
  `住院检查费` text  ,
  `住院检验费` text  ,
  `住院医疗服务费` text  ,
  `住院医保人次` text  ,
  `住院医保费用` text  ,
  `医保总控人次` text  ,
  `医保总控费用` text  ,
  `last_update` text  
) ;
DROP TABLE IF EXISTS `2024`;
CREATE TABLE `2024` LIKE `2023`;