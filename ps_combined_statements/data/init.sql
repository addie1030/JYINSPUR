CREATE OR REPLACE FUNCTION combined_statements_tax(period_str varchar, org_code varchar, flag int)
	RETURNS float AS
$result$
DECLARE
	result    float;
	account_1 float;
	account_2 float;
begin

	select sum(a.balance) into account_1
	from ac_tb a
			 left join combined_statements_organization org
					   on org.ref_company_id = a.company_id
	where a.code like '2221.03.01%' and org.code = org_code and replace(a.period, '-', '') = period_str;

	-- 期末余额
	select sum(kmye.ending_balance) into account_2
	from (select case
					 when (substring(at.code, 0, 2) in ('2', '4'))
						 then sum(at.balance * -1)
					 else sum(at.balance)
					 end as ending_balance
		  from ac_tb at
				   left join combined_statements_organization cso
							 on cso.ref_company_id = at.company_id
		  where replace(at.period, '-', '') = period_str and at.code like '2221%' and cso.code = org_code
		  group by at.code, at.balance) as kmye;


	if flag = 1
	then
		if account_1 > 0
		then
			result = account_1 + account_2;
		else
			result = account_2;
		end if;
	elseif flag = 2
	then
		if account_1 > 0
		then
			result = account_1;
		else
			result = 0;
		end if;
	end if;

	return result;

end
$result$
	language 'plpgsql'
	volatile;
